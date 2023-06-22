
const { transporters } = require("./transporters.js");
const { BaseBridgeProxy } = require("./proxies.js");
const { BaseBridgeConnection } = require("./connection.js");
const { proxymise, isRawObject } = require("./utils.js")
const util = require("util");



class BaseHandler {

  proxy = BaseBridgeProxy
  connection = BaseBridgeConnection;

  constructor() {
    let _this = this;

    this.proxies = new Map();
    this.message_handlers = new Map();

    this.formatters = {
      number: (_prop, x) => Number(x.value),
      float: (_prop, x) => Number.parseFloat(x.value),
      str: (_prop, x) => String(x.value),
      array: (_prop, x) => Array(x.value),
      object: (_prop, x) => x,
      set: (_prop, x) => Set(x.value),
      boolean: (_prop, x) => Boolean(x.value),
      callable_proxy: (_prop, x, use_kwargs=false) => {
        function __callable_proxy__(...args) {
          return proxymise(
            new Promise((resolve, reject) => {
              // console.log(typeof args);
              let kwargs = {};
              if (use_kwargs) {
                kwargs = args[args.length - 1]
                args = args.slice(0, args.length - 1)
              }

            _this
              .recieve({
                // session: PAGEID,
                action: "call_proxy",
                location: x.location,
                args: args,
                kwargs: kwargs
              })
              .then((result) => {
                // console.log("Res", result);
                resolve(_this.get_result(result));
              });
          })
          )
        };
        if (!use_kwargs) {
          __callable_proxy__.$ = _this.formatters.callable_proxy(null, x, true);
        }
        __callable_proxy__.__data__ = x;
        __callable_proxy__.__bridge_proxy__ = true;
        return __callable_proxy__;
      },
    //   bridge_proxy: (prop, x) => _this.get_proxy(x)
    };
  }

  random_id(length = 20) {
    return String(
      Math.random()
        .toString()
        .substring(2, length + 2)
    );
  }

  proxy_object(item) {
    let key;
    this.proxies.forEach((value, k) => {
        try {
          if (item == value) {
            key = k;
            return;
          }
        } catch (err) {}
    });
    if (key) {
      return key;
    } else {
      key = this.random_id();
      this.proxies.set(key, item);
      return key;
    }
  }

  generate_proxy(item) {
    let ret;
    if (item.obj_type == "callable_proxy") {
      ret = this.formatters.callable_proxy(null, item);
      ret.__is_proxy__ = true;
      ret.$ = this.formatters.callable_proxy(null, item, true);
      // ret = ret.bind(ret)
    } else {
      ret =  new this.proxy(this, item);
    }
    return ret;
  }

  get_proxy(key) {
    return this.proxies.get(String(key));
  }

  format_args(args) {
    return args.map(this.format_arg.bind(this));
  }

  encoder(key, value) { 
    let allow = false;
    try {
        Number(key);
        allow = true;
    } catch (err) {
      // console.log(err)
    }

    if (util.isArray(value)) {
      return value.map((val, ind) => {
        if (val) {
          return this.format_arg(val)
        } else {
          return val
        }
      });
    }

    if ((key !== "value" && key !== "response") || allow == false) {
      return value;
    }

    // console.log(key, util.types.isProxy(value))

    //   console.log(key, value)
    if (util.types.isProxy(value) || value?.__bridge_proxy__) {
      return { type: "bridge_proxy", obj_type: "reverse_proxy", location: String(value.__data__.location), reverse: true };
    }

    return this.format_arg(value);
  }

  decoder(key, value) {
      if (value instanceof Object) {
        // console.log("decoding:", key, value)
        if (value.message_id) {
          return value;
        }
        if (value.type == null && value.value == null && value.error) {
          return null
        }
        return this.get_result(value) || value
      }

      if (value instanceof Array) {
        return value.map((val, k) => this.decoder(k, val))
      }
      return value
  }

  async on_message(data) {
    // console.log("Message:", data)
    if (data.action) {
      let ret, raw = false;

      if (data.action == "get_primitive") {
        let res = this.handle_get_primitive(data);
        // console.log("[JS] Sending primitive:", res, "For:", data)
        raw = true;
        ret = { value: res, type: typeof res };
      } else {
        // console.log("Processing:", data)
        let response;
        try {
          response = await this.process_command(data);
          // console.log("Sending:", response)
          ret = response
        } catch (err) {
          // throw err
          // console.log(err)
          ret = {'error': err.message}
        }
      }
      ret.message_id = data.message_id;
      this.send(ret, !!raw)
    } else if (data.message_id) {
      let handler = this.message_handlers.get(data.message_id);
      if (handler) {
        handler(data);
        // this.message_handlers.delete(data.message_id);
        return;
      }
    }
  }

  send(response, raw = false) {
    this.transporter.send(response, raw);
  }

  recieve(message=null) {
    let _this = this;
    return new Promise((resolve, reject) => {
      let message_id = _this.random_id();
      
      if (message) {
        message.message_id = message_id
        // console.log("Send from:", message, message_id);
        _this.send(message);
      }

      _this.message_handlers.set(message_id, (data) => {
        // console.log("Recieved from:", data, message_id);
        try {
          // data = _this.parse(data);
          _this.message_handlers.delete(message_id);
          if (data.error !== undefined) {
            throw new Error(data.error)
          } else if (data.response !== undefined) (data = data.response)
          else if (data.value) (data = data.value)
          resolve(data);
        } catch (err) {
          return reject(err)
        }
      });
    });
  }

  async process_command(request) {
    let func = this["handle_" + request.action];
    if (!func) throw Error("Invalid action.");
    let ret = await func.call(this, request);
    return {response: ret};
  }

  handle_evaluate(request) {
    let ret = eval(request.value);
    return ret;
  }

  handle_eval_proxy(key, query) {
    let ret,
      target = this.get_proxy(req.location);
    if (target) {
      ret = eval(this.transform(query));
      ret = target(...args);
    }
    return ret;
  }

  async handle_await_proxy(key, query) {
    let ret,
      target = this.get_proxy(req.location);
    if (target) {
      ret = await target;
    }
    return ret;
  }

  async handle_call_proxy(req) {
    let ret,
      target = this.get_proxy(req.location);
    if (target) {
      let kwargs = [], args, i;
      let client = this;

      for (i in req.kwargs) {
        kwargs.push(req.kwargs[i]);
      }

      args = [...req.args, ...kwargs]

      ret = await target(...args);
    }
    return ret;
  }

  handle_delete_proxy(key, ..._args) {
    let ret,
      target = this.get_proxy(req.location);
    if (target) {
      ret = this.proxies.delete(key);
    }
    return ret;
  }

  handle_call_proxy_constructor(req) {
    let ret,
      target = this.get_proxy(req.location);
    if (target) {
      let kwargs = [], args, i;
      let client = this;

      for (i in req.kwargs) {
        kwargs.push((req.kwargs[i]));
      }

      args = [...req.args, ...kwargs]

      ret = new target(...args);
    }
    return ret;
  }

  handle_get_proxy_index(key, index) {
    let ret,
      target = this.get_proxy(req.location);
    if (target) {
      // console.log("Expression", "target." + index);
      ret = target[index];
      if (typeof ret == "function") {
        return ret.bind(target);
      }
    }

    return ret;
  }

  handle_get_proxy_attributes(req) {
    let ret,
      target = this.get_proxy(req.location);
    if (target) {
      ret = Reflect.ownKeys(target);
    }
    return ret;
  }

  handle_set_proxy_index(key, index, value) {
    let ret,
      target = this.get_proxy(req.location);
    if (target) {
      // console.log("Expression", "target." + attribute);
      target[index] = value;
    }
    return true;
  }
  handle_get_proxy_attribute(request) {
    let ret,
      target = this.get_proxy(request.location);
    if (target) {
      // console.log("Expression:", request);
      ret = eval("target." + request.target);
      // console.log("Returning:", ret, typeof ret, ret?.name);
      if (typeof ret == "function" && ret?.name !== "__proxy__bridge__target__") {
        try {
          return ret.bind(target);
        } catch (err) {}
      }
    }
    return ret;
  }

  handle_set_proxy_attribute(req) {
    let target = this.get_proxy(req.location);
    if (target) {
      // console.log("Expression", "target." + attribute);
      eval("target." + req.target + " = req.value");
    }

    return true;
  }

  handle_get_primitive(req) {
    let target = this.get_proxy(req.location);
    return target;
  }

  get_result(response, property=null) {
    let formatter;

    if (!response) return response;
    
    if (isRawObject(response)) {
      let is_proxy = (response.type == "bridge_proxy")
  
      // console.log(is_proxy, response)
  
      if (response.expression) {
        return eval((response.expression))
      } else if ((is_proxy || response.type) && response.location) {
        // this.proxies.push(response.location);
        if (response.reverse) return this.get_proxy(response.location)
        return this.generate_proxy(response);
      } else if (this.formatters[response.type]) {
        return this.formatters[response.type](property, response);
      } else if (response.value) {
          return response.value
      } else if (response.error) {
        throw Error(response.error);
      }
    }
    return response;
  }

}

class NodeBridgeClient extends BaseHandler {
  constructor(options) {
    super()
    this.options = options || {};
  }

  start() {
    let transporter = transporters[this.options.mode];
    if (!transporter) {
      throw new Error("ArgumentError: Invalid mode specified.");
    }

    this.transporter = new transporter();
    this.transporter.start_client(
      this.on_message.bind(this),
      this.options,
      this
    );
  }

  format_arg(value) {
    let location;
    let value_type = typeof value;

    if (util.isNullOrUndefined(value)) {
      return null
    }

    if (value_type == "function" && (value?.name === "__proxy__bridge__target__" || value?.name === "bound __proxy__bridge__target__")) {
      return { type: "bridge_proxy", obj_type: "reverse_proxy", location: String(value.__data__.location), reverse: true };
    }

    if (value_type == "string") {
      try {
        let is_number;
        try {
          is_number = new Number(value);
        } catch (err) {}

        if (!is_number) {
          let t = new Date(value);
          location = this.proxy_object(t);
          return { type: "bridge_proxy", obj_type: "date", location: location };
        }
      } catch (err) {}
    }

    if (value_type === 'number' ||
      util.isArray(value) ||
      value_type === 'string' ||
      value_type == "boolean"
    ) {
        return value
      // return { type: "bridge_proxy", obj_type: "number", location: location };
    }

    location = this.proxy_object(value);

    if (util.isSymbol(value)) {
      return { type: "bridge_proxy", obj_type: "symbol", location: location };
    }

    if (util.isNumber(value)) {
      return { type: "bridge_proxy", obj_type: "number", location: location };
    }

    if (util.isBuffer(value)) {
      return { type: "bridge_proxy", obj_type: "bytes", location: location }
    }

    if (util.isString(value)) {
      return { type: "bridge_proxy", obj_type: "string", location: location };
    }

    if (util.types.isSet(value)) {
      return { type: "bridge_proxy", obj_type: "set", location: location };
    }

    if (util.isArray(value)) {
      return { type: "bridge_proxy", obj_type: "array", location: location };
    }

    if (value instanceof Event) {
      return { type: "bridge_proxy", obj_type: "event", location: location };
    }

    if (util.isFunction(value)) {
      return { type: "bridge_proxy", obj_type: "function", location: location };
    }

    if (util.isDate(value)) {
      return { type: "bridge_proxy", obj_type: "date", location: location };
    }
    
    if (value_type == 'object') {
        value_type = '';
    }

    return { type: "bridge_proxy", obj_type: value_type, location: location };
  }
}
