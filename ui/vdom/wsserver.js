
class WebSocketBackend {

  constructor(url, options={}) {
    this.ws = new WebSocket((options.prefix || "ws://") + url);
    this.ws.onopen = options.onopen;
    this.ws.onclose = options.onclose;
    this.ws.onerror = ev => options.onerror("");
    this.ws.onmessage = ev => options.onmessage(ev.data);

    this.OPEN =this.ws.OPEN;
    this.CLOSED =this.ws.CLOSED;
    this.CLOSING =this.ws.CLOSING;
    this.CONNECTING =this.ws.CONNECTING;
  }

  send(message) {
  this.ws.send(message);
  }

  getState() {
    return this.ws.readyState;
  }
}

class HTTPBackend {
  constructor(url, options) {
    this.url = (options.prefix || "http://") + url;
    this.options = options;

    this.CONNECTING = 1;
    this.OPEN = 2;
    this.CLOSING = 3;
    this.CLOSED = 4;
  }

  send(data) {
    let _this= this;
    let request = new Request(this.url, {
      method: "POST",
      body: data,
      credentials: "same-origin",
      headers: [
        ["Content-Type", "application/json;charset=UTF-8"]
      ]
    })
    fetch(request).then(response => {
      if (response.status == 200) {
        return response.json()
      } else {
        _this.options.onerror(response.text);
        return null;
      }
    }).then(data => {
      data && _this.options.onmessage(data)
    })
  }

  getState() {
    return this.OPEN;
  }
}

class SocketIOBackend {
  constructor(url, options={}) {
    this.socket = io({
      "path": "/__process_svr0/"
    });
    this.options = options;

    this.CONNECTING = 1;
    this.OPEN = 2;
    this.CLOSING = 3;
    this.CLOSED = 4;

    this.socket.on("message", (data) => {
      console.log(data);
      this.options.onmessage(data);
    })
  }

  send(message) {
    this.socket.emit("message", message);
  }

  getState() {
    return this.OPEN;
  }
}

class ClientContext {
  constructor(address, options = null) {
    this.backend_server = WebSocketBackend;

    this.address = address;
    this.options = options || {};
    this.tasks = [];

    this.proxies = new Map();
    this.pyproxies = [];
    this.transformer = null;

    this.messge_handlers = new Map()

    this.awaitingResponse = false;

    let _this = this;

    this.formatters = {
      int: (_prop, x) => new Number(x.value),
      float: (_prop, x) => Number.parseFloat(x.value),
      str: (_prop, x) => new String(x.value),
      list: (_prop, x) => new Array(x.value),
      dict: (_prop, x) => x,
      set: (_prop, x) => new Set(x.value),
      bool: (_prop, x) => new Boolean(x.value),
      function: (prop, _x) => {
        return function (...args) {
          return _this.send({
            // session: PAGEID,
            task: "async",
            function: prop,
            args: args,
          });
        };
      },
      method: (prop, _x) => {
        return function (...args) {
          return _this.recieve({
            // session: PAGEID,
            task: "async",
            function: prop,
            args: args,
          });
        };
      },
      callable_proxy: (prop, x, use_kwargs=false) => {
        return function (...args) {
          return _this.proxymise(
            new Promise((resolve, reject) => {
              // console.log(typeof args);
              let kwargs = {};
              if (use_kwargs) {
                kwargs = args[args.length - 1]
              }

            _this
              .recieve({
                // session: PAGEID,
                task: "call_proxy",
                target: x.location,
                args: args,
              })
              .then((result) => {
                // console.log("Res", result);
                resolve(_this.get_result(result, prop));
              });
          })
          )
        };
      },
      jsproxy: (prop, x) => _this.getProxyObject(x.value)
    };

    this.handlers = {
      construct(target, argumentsList) {
        if (target.__proxy__) target = target();
        return _this.proxymise(Reflect.construct(target, argumentsList));
      },

      get(target, property, receiver) {
        if (target.__proxy__) target = target();
        if (property !== 'then' && property !== 'catch' && typeof target.then === 'function') {
          return _this.proxymise(target.then(value => _this.get(value, property, receiver)));
        }
        return _this.proxymise(_this.get(target, property, receiver));
      },

      apply(target, thisArg, argumentsList) {
        if (target.__proxy__) target = target();
        if (typeof target.then === 'function') {
          return _this.proxymise(target.then(value => Reflect.apply(value, thisArg, argumentsList)));
        }
        return _this.proxymise(Reflect.apply(target, thisArg, argumentsList));
      }
    }

    this.server = new Proxy(
      {},
      {
        get: function(_target, property) {
          return _this.proxymise(
            new Promise((r, rj) => {

              _this.recieve({
                // session: PAGEID,
                task: "attribute",
                item: property.endsWith("_") ? property.substring(0, property.length -1) : property,
              }).then(result => {
                if (property.endsWith("_") && result.location) {
                  return r(_this.formatters.callable_proxy(property.substring(0, property.length -1), result, true)); 
                }
                result = _this.get_result(result, property);
                if (result == undefined) {
                  if (property !== 'then' && property !== 'catch' && typeof target.then === 'function') {
                    rj("No attribute name: " + property);
                  }
                } else {
                  r(result);
                }
              })
            })
          );
        },
      }
    );

    this.app = new Proxy(
      {},
      {
        get: function (_target, prop) {
          return handleAppProperty(prop);
        },
        set: function (_target, prop, value) {
          return handleAppSetProperty(prop, value);
        },
      }
    );

    if (this.options.observe_mutations) {
      this.mutations = [];
      this.observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
          this.mutations.push({
            addedNodes: ELementsToList(mutation.addedNodes),
            attributeName: mutation.attributeName,
            attributeNamespace: mutation.attributeNamespace,
            nextSibling: ELementToDict(mutation.nextSibling),
            oldValue: mutation.oldValue,
            previousSibling: ELementToDict(mutation.previousSibling),
            removedNodes: ELementsToList(mutation.removedNodes),
            target: xpath_generator(mutation.target),
            type: mutation.type,
          });
        }
        this.send({
          // session: PAGEID,
          task: "update_dom",
          modifications: this.mutations,
        });
      });
    }

    window.onunload = () => {
      this.pyproxies.forEach((key) => {
        _this.send({
          // session: PAGEID,
          task: "delete_proxy",
          target: key,
        })
      })
      this.sendSignal("disconnected");
      return true;
    }

    this.py = new Proxy(
      {
        import(lib) {
          return _this.proxymise(
            new Promise((r, rj) => {
              _this.recieve({
                // session: PAGEID,
                task: "import",
                item: lib,
              }).then(result => {
                result = _this.get_result(result, lib);
                if (result == undefined) {
                  rj("No module named: " + lib);
                } else {
                  r(result);
                }
              })
            })
          );
        }
      }, {
        get(target, prop, reciever) {
          if (target[prop]) {
            return target[prop]
          }
          return _this.proxymise(
            new Promise((r, rj) => {
              _this.recieve({
                // session: PAGEID,
                task: "builtin",
                item: prop.endsWith("_") ? prop.substring(0, prop.length -1) : prop,
              }).then(result => {
                if (prop.endsWith("_") && result.location) {
                  return r(_this.formatters.callable_proxy(prop.substring(0, prop.length -1), result, true)); 
                }
                result = _this.get_result(result, prop);
                if (result == undefined) {
                  if (prop !== 'then' && prop !== 'catch' && typeof target.then === 'function') {
                    rj("No item named: " + prop);
                  }
                } else {
                  r(result);
                }
              })
            })
          );
        }
      }
    )
  }

  transform(code, ...opts) {
    if (this.transformer == "babel") {
      return babel.transform(code, ...opts).code
    }
    return code
  }

  randomId(length = 20) {
    return String(
      Math.random()
        .toString()
        .substring(2, length + 2)
    );
  }

  proxyObject(item) {
    let key;
    this.proxies.forEach((value, k) => {
      if (item == value) {
        key = k;
        return;
      }
    });
    if (key) {
      return key;
    } else {
      key = this.randomId();
      this.proxies.set(key, item);
      return key;
    }
  }

  getProxyObject(key) {
    return this.proxies.get(String(key));
  }

  evalProxy(key, query) {
    let ret,
      target = this.getProxyObject(key);
    if (target) {
      ret = eval(this.transform(query));
      ret = target(...args);
    }
    return ret;
  }

  callProxy(key, ...args) {
    let ret,
      target = this.getProxyObject(key);
    if (target) {
      ret = target(...args);
    }
    return ret;
  }

  delProxy(key, ..._args) {
    let ret,
      target = this.getProxyObject(key);
    if (target) {
      ret = this.proxies.delete(key);
    }
    return ret;
  }

  callProxyConstructor(key, ...args) {
    let ret,
      target = this.getProxyObject(key);
    if (target) {
      ret = new target(...args);
    }
    return ret;
  }

  getProxyIndex(key, index) {
    let ret,
      target = this.getProxyObject(key);
    if (target) {
      // console.log("Expression", "target." + index);
      ret = target[index];
      if (typeof ret == "function") {
        return ret.bind(target);
      }
    }

    return ret;
  }

  setProxyIndex(key, index, value) {
    let ret,
      target = this.getProxyObject(key);
    if (target) {
      // console.log("Expression", "target." + attribute);
      target[index] = value
    }

    return true;
  }
  getProxyAttribute(key, attribute) {
    let ret,
      target = this.getProxyObject(key);
    if (target) {
      // console.log("Expression", "target." + attribute);
      ret = eval("target." + attribute);
      if (typeof ret == "function") {
        return ret.bind(target);
      }
    }

    return ret;
  }
  setProxyAttribute(key, attribute, value) {
    let target = this.getProxyObject(key);
    if (target) {
      // console.log("Expression", "target." + attribute);
      eval("(target." + attribute + ") = value");
    }

    return true;
  }

  connect() {
    let options = {};
    options.onopen = this.on_open.bind(this);
    options.onclose = this.on_close.bind(this);
    options.onerror = this.on_error.bind(this);
    options.onmessage = this.on_message.bind(this);

    this.backend = new this.backend_server(this.address, options);
  }

  handleApp(property, args) {
    this.send({
      // session: PAGEID,
      task: "run",
      block: true,
      function: property,
      args: args,
    });
  }

  handleAppProperty(property) {
    this.send({
      // session: PAGEID,
      task: "get",
      block: true,
      expression: property,
    });
  }

  handleAppSetProperty(property, value) {
    this.send({
      // session: PAGEID,
      task: "set",
      property: property,
      value: value,
    });
    return value;
  }

  formatArg(value) {
    let key;

    if (
      value instanceof Number ||
      value instanceof String ||
      value instanceof Set
    ) {
      return value;
    }

    let value_type = typeof value;
    // console.log(
    //   value,
    //   value.constructor.toString().split(" ")[0],
    //   value_type,
    //   "\n"
    // );

    if (value_type =="symbol") {
      key = this.proxyObject(value);   
      return { type: "js_proxy", obj_type: "symbol", key: key }; 
    }

    if (value_type == "string") {
      try {
        let is_number;
        try {
          is_number = new Number(value)
        } catch (err) {}

        if (!is_number) {
          let t = new Date(value);
          console.log(value);
          key = this.proxyObject(t);
          return { type: "js_proxy", obj_type: "date", key: key };
        }

      } catch (err) {}
    }

    if (value instanceof Event) {
      key = this.proxyObject(value);
      return { type: "js_proxy", obj_type: "event", key: key };
    }

    if (value instanceof NodeList) {
      let ret = [];
      value.forEach((node) => {
        ret.push(this.formatArg(node));
      })
      return { type: "js_proxy", obj_type: "nodelist", key: key, value: ret };
    }

    if (value instanceof Date) {
      key = this.proxyObject(value);
      return { type: "js_proxy", obj_type: "class", key: key };
    }

    switch (value.constructor.toString().split(" ")[0]) {
      case "function":
        if (!(value_type == "function" || value_type == "object")) {
          return value;
        }

        key = this.proxyObject(value);

        if (value instanceof HTMLElement || value instanceof Node) {
          return { type: "js_proxy", obj_type: "element", key: key };
        }

        return { type: "js_proxy", obj_type: value_type, key: key };

      case "class":
        key = this.proxyObject(value);
        return { type: "js_proxy", obj_type: "class", key: key };

      default:
        key = this.proxyObject(value);
        return { type: "js_proxy", obj_type: value_type, key: key };
      // default:
      //   return value
    }
  };

  stringify(message) {
    let _this = this;

    return JSON.stringify(message, (key, value) => {
      let allow = false;
      try {
        Number(key);
        allow = true;
      } catch (err) {}
  
      if (
        value === undefined ||
        value === null ||
        !(key === "value" || key === "args") ||
        allow == false
      ) {
        return value;
      }

      if (value instanceof Array) {
        return value.map(_this.formatArg.bind(_this))
      }

      return _this.formatArg.bind(_this)(value);
    });
  }

  parse(data) {
    let ret = JSON.parse(data);
    return ret;
  }

  sendSignal(signal, ...args) {
    this.send({
      // session: PAGEID,
      task: "signal",
      signal: signal,
      args: args,
    });
    return null;
  }

  send(message) {
    message.namespace = NAMESPACE;
    // console.log("Message:", message);

    if (this.backend.getState() == this.backend.OPEN) {
      try {
        let m = this.stringify(message);
        // console.log("Sent:", m);
        this.backend.send(m);
      } catch (err) {
        // throw err;
        this.tasks.push(() => {
          this.backend.send(this.stringify(message));
        });
      }
    } else if (
      this.backend.readyState == this.backend.CLOSED ||
      this.backend.readyState == this.backend.CLOSING
    ) {
      console.log("WebSocket Closed.");
    } else {
      this.tasks.push(() => {
        this.send(message);
      });
    }
  }

  handle_tasks(max_retry=10, interval=0.1) {
    let tries = 0;
    this.intervalId = setInterval(() => {
      if (tries >= max_retry) {
        return clearInterval(this.intervalId);
      }

      if (this.tasks) {
        tries = 0;
        for (let index = 0; index < this.tasks.length; index++) {
          let task = this.tasks.shift();
          task && task();
        }
      } else {
        tries++;
      }
    }, interval * 1000);
  }

  recieve(message = null) {
    let _this = this;
    return new Promise((resolve, _reject) => {
      let message_id = _this.randomId();
      
      if (message) {
        message.message_id = message_id
        console.log("Send from:", message);
        _this.send(message);
        _this.awaitingResponse = true;
      }

      function messageHandler(data) {
        let recv = data;
        console.log("Recieved from:", recv);

        try {
          // recv = _this.parse(recv);
          if (recv.expression) {
            eval(_this.transform(recv.expression))
          } else {
            _this.awaitingResponse = false;
            resolve(recv);
          }
        } catch (err) {}
      };

      _this.messge_handlers.set(message_id, messageHandler);
    });
  }

  get_result(response, property=null) {
    let formatter;

    if (!response) return response;

    if (response.expression) {
      return resolve(eval(this.transform(response.expression)))
    } else if ((formatter = this.formatters[response.type])) {
      return formatter(property, response);
    } else if (response.location) {
      this.pyproxies.push(response.location);
      return this.PyProxy(response);
    } else if (response.error) {
      throw Error(response.error);
    }
    return undefined;
  }

  PyProxy(res) {
    let _this = this;
    let proxy = new Proxy(
      (function(){}),
      {
        get: function(target, property) {
          return new Promise((resolve, reject) => {

            if (target[property]) {
              return resolve(target[property])
            }

            if (property === 'then') {
              return resolve(target.then);
            } else if (property === 'catch') {
              return resolve(target.catch);
            }

            if (property === "toJSON" || property == "constructor") {
              return undefined;
            }

            console.log(res, property);

            _this
              .recieve({
                // session: PAGEID,
                task: "get_proxy_attribute",
                prop: property.endsWith("_") ? property.substring(0, property.length -1) : property,
                target: res.location,
              })
              .then((result) => {
                // console.log("\nResult: ", result);
                try {
                  if (property.endsWith("_") && result.location) {
                    return resolve(_this.formatters.callable_proxy(property.substring(0, property.length -1), result, true)); 
                  }
                  result = _this.get_result(result, property);
                } catch (error) {
                  return undefined;
                }
  
                if (result == undefined) {
                  if (property !== "then") {
                    return reject("No attribute name: " + property);
                  }
                } else {
                  resolve(result);
                }
              });
          });
        },
        set: function(target, property, value) {
          return new Promise((resolve, _reject) => {
            _this
              .recieve({
                // session: PAGEID,
                task: "set_proxy_attribute",
                prop: property,
                target: res.location,
                value: value,
              })
              .then((result) => resolve(result.value));
          });
        },
        ownKeys: function(target) {
          return new Promise((resolve, _reject) => {
            _this
              .recieve({
                // session: PAGEID,
                task: "get_proxy_attributes",
                target: res.location,
              })
              .then((result) => {
                resolve(Object.keys(result.value));
              });
          });
        },
        deleteProperty: function(target, prop) {
          // to intercept property deletion
          return new Promise((resolve, _reject) => {
            _this
              .recieve({
                // session: PAGEID,
                task: "delete_proxy_attribute",
                prop: prop,
                target: res.location,
                value: prop,
              })
              .then((result) => resolve(result.value));
          });
        },
        has: function(target, prop) {
          return new Promise((resolve, _reject) => {
            _this
              .recieve({
                // session: PAGEID,
                task: "has_proxy_attribute",
                prop: prop,
                target: res.location,
                value: prop,
              })
              .then((result) => resolve(result.value));
          });
        },
        apply: function(target, _thisArg, args) {
          return new Promise((resolve, reject) => {
            _this
              .recieve({
                // session: PAGEID,
                task: "call_proxy",
                target: res.location,
                args: args,
              })
              .then((result) => resolve(_this.get_result(result)));
          });
        },
        construct: function(target, args) {
          return new Promise((resolve, reject) => {
            _this
              .recieve({
                // session: PAGEID,
                task: "call_proxy",
                target: res.location,
                args: args,
              })
              .then((result) => resolve(_this.get_result(result)));
          });
        }
      }
    );
    return proxy;
  }

  proxymise(target) {
    if (typeof target === 'object') {
      const proxy = () => target;
      proxy.__proxy__ = true;
      return new Proxy(proxy, this.handlers);
    }
    return typeof target === 'function' ? new Proxy(target, this.handlers) : target;
  };
  
  get(target, property, receiver) {
    const value = typeof target === 'object' ? Reflect.get(target, property, receiver) : target[property];
    if (typeof value === 'function' && typeof value.bind === 'function') {
      return Object.assign(value.bind(target), value);
    }
    return value;
  };

  on_open() {
    while (this.tasks.length < 1 && this.backend.getState() == this.backend.OPEN) {
      clearInterval(this.intervalId);
      this.sendSignal("connected");
      return null;
    }
  }

  on_message(response) {
    if (response) {
      let result = this.parse(response);

      if (result.message_id) {
        let handler = this.messge_handlers.get(result.message_id);
        if (handler) {
          handler(result);
          this.messge_handlers.delete(result.message_id);
          return;
        }
      }

      if (result.expression) {
        try {
          //console.log("Next async task", request.responseText) // DEBUG
          // console.log(response);
          let return_value;
          return_value = eval(this.transform(result.expression));
          // console.log(return_value);
          // setTimeout(evalBrowser, 1);
        } catch (e) {
          console.log("ERROR", e.message); // DEBUG
          setTimeout(() => {
            this.sendErrorToServer(result.expression, e.message);
            //   evalBrowser();
          }, 1);
        }
      } else {
        if (result.error && result.error !== true) {
          console.log("ERROR", result["error"]);
          throw result["error"];
          // return null;
        }
        if (result["type"] == "expression") {
          return eval(this.transform(result["expression"]));
        } else {
          return result["value"];
        }
      }
    }
  }

  on_error(data) {
    console.log("ERROR async: ", data);
  }

  on_close(_ev) {
    console.log("Websocked enter closed state.");
  }

  evalBrowser() {
    // this.send({ session: PAGEID, task: "next" }));
  }

  sendFromBrowserToServer(expression, query = null) {
    var value;
    var error = "";
    try {
      // console.log("Evaluate", query, expression); // DEBUG
      value = eval(this.transform(expression));
      // console.log("Result", value);
    } catch (e) {
      value = 0;
      error = e.message + ": '" + expression + "'";
      console.log("ERROR", query, error);
    }
    this.send({
      // session: PAGEID,
      task: "state",
      value: value || null,
      query: query,
      error: error,
    });
  }
  sendErrorToServer(expr, e) {
    this.send({ /*session: PAGEID,*/ task: "error", error: e, expr: expr });
  }

  closeBrowserWindow() {
    this.send({ /*session: PAGEID,*/ task: "unload" });
  }

  get_element_index(node) {
    var temp = [];
    var parentChildrens = node.parentElement?.children || [];
    var childrenNr = node.parentElement?.children.length || 0;

    for (var i = 0; i <= childrenNr; i++) {
      if (typeof parentChildrens[i] !== "undefined") {
        if (parentChildrens[i].tagName.toLowerCase() == node.localName) {
          temp.push(parentChildrens[i]);
        }
      }
    }
    return temp;
  }

  generate_xpath(e) {
    var node = e;

    var temp_one = this.get_element_index(node);
    var last_node_index = Array.prototype.indexOf.call(temp_one, node);

    if (temp_one.length == 1) {
      var path = "/" + node.localName;
    } else if (temp_one.length > 1) {
      last_node_index = last_node_index + 1;
      var path = "/" + node.localName + "[" + last_node_index + "]";
    }

    while (node != document.html && node.parentNode !== null) {
      node = node.parentNode;

      /* When loop reaches the last element of the dom (body)*/
      if (node.localName == "body") {
        var current = "/body";
        path = current + path;
        break;
      }

      /* if the node has id attribute and is not the last element */
      if (node.id != "" && node.localName != "body") {
        var current = "/" + node.localName + "[@id='" + node.id + "']";
        path = current + path;
        break;
      }

      /* if the node has class attribute and has no id attribute or is not the last element */
      if (node.id == "" && node.localName != "body") {
        if (node.parentNode !== null) {
          var temp = get_element_index(node);
          var node_index = Array.prototype.indexOf.call(temp, node);

          if (temp.length == 1) {
            var current = "/" + node.localName;
          } else if (temp.length > 1) {
            node_index = node_index + 1;
            var current = "/" + node.localName + "[" + node_index + "]";
          }
        }
      }
      path = current + path;
    }
    return "/" + path;
  }

  ELementToDict(element) {
    if (element?.nodeType === 1) {
      return html2json(element.outerHTML);
    }
    return {};
  }

  ELementsToList(elements) {
    let ret = [];
    elements.forEach((item) => {
      ret.push(ELementToDict(item));
    });
    return ret;
  }
}
