(function (f) { if (typeof exports === "object" && typeof module !== "undefined") { module.exports = f() } else if (typeof define === "function" && define.amd) { define([], f) } else { var g; if (typeof window !== "undefined") { g = window } else if (typeof global !== "undefined") { g = global } else if (typeof self !== "undefined") { g = self } else { g = this } g.JSBridge = f() } })(function () {
  var define, module, exports; return (function () { function r(e, n, t) { function o(i, f) { if (!n[i]) { if (!e[i]) { var c = "function" == typeof require && require; if (!f && c) return c(i, !0); if (u) return u(i, !0); var a = new Error("Cannot find module '" + i + "'"); throw a.code = "MODULE_NOT_FOUND", a } var p = n[i] = { exports: {} }; e[i][0].call(p.exports, function (r) { var n = e[i][1][r]; return o(n || r) }, p, p.exports, r, e, n, t) } return n[i].exports } for (var u = "function" == typeof require && require, i = 0; i < t.length; i++)o(t[i]); return o } return r })()({
    1: [function (require, module, exports) {

    }, {}], 2: [function (require, module, exports) {
      (function (global) {
        (function () {
          'use strict';

          var possibleNames = [
            'BigInt64Array',
            'BigUint64Array',
            'Float32Array',
            'Float64Array',
            'Int16Array',
            'Int32Array',
            'Int8Array',
            'Uint16Array',
            'Uint32Array',
            'Uint8Array',
            'Uint8ClampedArray'
          ];

          var g = typeof globalThis === 'undefined' ? global : globalThis;

          module.exports = function availableTypedArrays() {
            var out = [];
            for (var i = 0; i < possibleNames.length; i++) {
              if (typeof g[possibleNames[i]] === 'function') {
                out[out.length] = possibleNames[i];
              }
            }
            return out;
          };

        }).call(this)
      }).call(this, typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})
    }, {}], 3: [function (require, module, exports) {
      'use strict';

      var GetIntrinsic = require('get-intrinsic');

      var callBind = require('./');

      var $indexOf = callBind(GetIntrinsic('String.prototype.indexOf'));

      module.exports = function callBoundIntrinsic(name, allowMissing) {
        var intrinsic = GetIntrinsic(name, !!allowMissing);
        if (typeof intrinsic === 'function' && $indexOf(name, '.prototype.') > -1) {
          return callBind(intrinsic);
        }
        return intrinsic;
      };

    }, { "./": 4, "get-intrinsic": 8 }], 4: [function (require, module, exports) {
      'use strict';

      var bind = require('function-bind');
      var GetIntrinsic = require('get-intrinsic');

      var $apply = GetIntrinsic('%Function.prototype.apply%');
      var $call = GetIntrinsic('%Function.prototype.call%');
      var $reflectApply = GetIntrinsic('%Reflect.apply%', true) || bind.call($call, $apply);

      var $gOPD = GetIntrinsic('%Object.getOwnPropertyDescriptor%', true);
      var $defineProperty = GetIntrinsic('%Object.defineProperty%', true);
      var $max = GetIntrinsic('%Math.max%');

      if ($defineProperty) {
        try {
          $defineProperty({}, 'a', { value: 1 });
        } catch (e) {
          // IE 8 has a broken defineProperty
          $defineProperty = null;
        }
      }

      module.exports = function callBind(originalFunction) {
        var func = $reflectApply(bind, $call, arguments);
        if ($gOPD && $defineProperty) {
          var desc = $gOPD(func, 'length');
          if (desc.configurable) {
            // original length, plus the receiver, minus any additional arguments (after the receiver)
            $defineProperty(
              func,
              'length',
              { value: 1 + $max(0, originalFunction.length - (arguments.length - 1)) }
            );
          }
        }
        return func;
      };

      var applyBind = function applyBind() {
        return $reflectApply(bind, $apply, arguments);
      };

      if ($defineProperty) {
        $defineProperty(module.exports, 'apply', { value: applyBind });
      } else {
        module.exports.apply = applyBind;
      }

    }, { "function-bind": 7, "get-intrinsic": 8 }], 5: [function (require, module, exports) {
      'use strict';

      var isCallable = require('is-callable');

      var toStr = Object.prototype.toString;
      var hasOwnProperty = Object.prototype.hasOwnProperty;

      var forEachArray = function forEachArray(array, iterator, receiver) {
        for (var i = 0, len = array.length; i < len; i++) {
          if (hasOwnProperty.call(array, i)) {
            if (receiver == null) {
              iterator(array[i], i, array);
            } else {
              iterator.call(receiver, array[i], i, array);
            }
          }
        }
      };

      var forEachString = function forEachString(string, iterator, receiver) {
        for (var i = 0, len = string.length; i < len; i++) {
          // no such thing as a sparse string.
          if (receiver == null) {
            iterator(string.charAt(i), i, string);
          } else {
            iterator.call(receiver, string.charAt(i), i, string);
          }
        }
      };

      var forEachObject = function forEachObject(object, iterator, receiver) {
        for (var k in object) {
          if (hasOwnProperty.call(object, k)) {
            if (receiver == null) {
              iterator(object[k], k, object);
            } else {
              iterator.call(receiver, object[k], k, object);
            }
          }
        }
      };

      var forEach = function forEach(list, iterator, thisArg) {
        if (!isCallable(iterator)) {
          throw new TypeError('iterator must be a function');
        }

        var receiver;
        if (arguments.length >= 3) {
          receiver = thisArg;
        }

        if (toStr.call(list) === '[object Array]') {
          forEachArray(list, iterator, receiver);
        } else if (typeof list === 'string') {
          forEachString(list, iterator, receiver);
        } else {
          forEachObject(list, iterator, receiver);
        }
      };

      module.exports = forEach;

    }, { "is-callable": 16 }], 6: [function (require, module, exports) {
      'use strict';

      /* eslint no-invalid-this: 1 */

      var ERROR_MESSAGE = 'Function.prototype.bind called on incompatible ';
      var slice = Array.prototype.slice;
      var toStr = Object.prototype.toString;
      var funcType = '[object Function]';

      module.exports = function bind(that) {
        var target = this;
        if (typeof target !== 'function' || toStr.call(target) !== funcType) {
          throw new TypeError(ERROR_MESSAGE + target);
        }
        var args = slice.call(arguments, 1);

        var bound;
        var binder = function () {
          if (this instanceof bound) {
            var result = target.apply(
              this,
              args.concat(slice.call(arguments))
            );
            if (Object(result) === result) {
              return result;
            }
            return this;
          } else {
            return target.apply(
              that,
              args.concat(slice.call(arguments))
            );
          }
        };

        var boundLength = Math.max(0, target.length - args.length);
        var boundArgs = [];
        for (var i = 0; i < boundLength; i++) {
          boundArgs.push('$' + i);
        }

        bound = Function('binder', 'return function (' + boundArgs.join(',') + '){ return binder.apply(this,arguments); }')(binder);

        if (target.prototype) {
          var Empty = function Empty() { };
          Empty.prototype = target.prototype;
          bound.prototype = new Empty();
          Empty.prototype = null;
        }

        return bound;
      };

    }, {}], 7: [function (require, module, exports) {
      'use strict';

      var implementation = require('./implementation');

      module.exports = Function.prototype.bind || implementation;

    }, { "./implementation": 6 }], 8: [function (require, module, exports) {
      'use strict';

      var undefined;

      var $SyntaxError = SyntaxError;
      var $Function = Function;
      var $TypeError = TypeError;

      // eslint-disable-next-line consistent-return
      var getEvalledConstructor = function (expressionSyntax) {
        try {
          return $Function('"use strict"; return (' + expressionSyntax + ').constructor;')();
        } catch (e) { }
      };

      var $gOPD = Object.getOwnPropertyDescriptor;
      if ($gOPD) {
        try {
          $gOPD({}, '');
        } catch (e) {
          $gOPD = null; // this is IE 8, which has a broken gOPD
        }
      }

      var throwTypeError = function () {
        throw new $TypeError();
      };
      var ThrowTypeError = $gOPD
        ? (function () {
          try {
            // eslint-disable-next-line no-unused-expressions, no-caller, no-restricted-properties
            arguments.callee; // IE 8 does not throw here
            return throwTypeError;
          } catch (calleeThrows) {
            try {
              // IE 8 throws on Object.getOwnPropertyDescriptor(arguments, '')
              return $gOPD(arguments, 'callee').get;
            } catch (gOPDthrows) {
              return throwTypeError;
            }
          }
        }())
        : throwTypeError;

      var hasSymbols = require('has-symbols')();

      var getProto = Object.getPrototypeOf || function (x) { return x.__proto__; }; // eslint-disable-line no-proto

      var needsEval = {};

      var TypedArray = typeof Uint8Array === 'undefined' ? undefined : getProto(Uint8Array);

      var INTRINSICS = {
        '%AggregateError%': typeof AggregateError === 'undefined' ? undefined : AggregateError,
        '%Array%': Array,
        '%ArrayBuffer%': typeof ArrayBuffer === 'undefined' ? undefined : ArrayBuffer,
        '%ArrayIteratorPrototype%': hasSymbols ? getProto([][Symbol.iterator]()) : undefined,
        '%AsyncFromSyncIteratorPrototype%': undefined,
        '%AsyncFunction%': needsEval,
        '%AsyncGenerator%': needsEval,
        '%AsyncGeneratorFunction%': needsEval,
        '%AsyncIteratorPrototype%': needsEval,
        '%Atomics%': typeof Atomics === 'undefined' ? undefined : Atomics,
        '%BigInt%': typeof BigInt === 'undefined' ? undefined : BigInt,
        '%BigInt64Array%': typeof BigInt64Array === 'undefined' ? undefined : BigInt64Array,
        '%BigUint64Array%': typeof BigUint64Array === 'undefined' ? undefined : BigUint64Array,
        '%Boolean%': Boolean,
        '%DataView%': typeof DataView === 'undefined' ? undefined : DataView,
        '%Date%': Date,
        '%decodeURI%': decodeURI,
        '%decodeURIComponent%': decodeURIComponent,
        '%encodeURI%': encodeURI,
        '%encodeURIComponent%': encodeURIComponent,
        '%Error%': Error,
        '%eval%': eval, // eslint-disable-line no-eval
        '%EvalError%': EvalError,
        '%Float32Array%': typeof Float32Array === 'undefined' ? undefined : Float32Array,
        '%Float64Array%': typeof Float64Array === 'undefined' ? undefined : Float64Array,
        '%FinalizationRegistry%': typeof FinalizationRegistry === 'undefined' ? undefined : FinalizationRegistry,
        '%Function%': $Function,
        '%GeneratorFunction%': needsEval,
        '%Int8Array%': typeof Int8Array === 'undefined' ? undefined : Int8Array,
        '%Int16Array%': typeof Int16Array === 'undefined' ? undefined : Int16Array,
        '%Int32Array%': typeof Int32Array === 'undefined' ? undefined : Int32Array,
        '%isFinite%': isFinite,
        '%isNaN%': isNaN,
        '%IteratorPrototype%': hasSymbols ? getProto(getProto([][Symbol.iterator]())) : undefined,
        '%JSON%': typeof JSON === 'object' ? JSON : undefined,
        '%Map%': typeof Map === 'undefined' ? undefined : Map,
        '%MapIteratorPrototype%': typeof Map === 'undefined' || !hasSymbols ? undefined : getProto(new Map()[Symbol.iterator]()),
        '%Math%': Math,
        '%Number%': Number,
        '%Object%': Object,
        '%parseFloat%': parseFloat,
        '%parseInt%': parseInt,
        '%Promise%': typeof Promise === 'undefined' ? undefined : Promise,
        '%Proxy%': typeof Proxy === 'undefined' ? undefined : Proxy,
        '%RangeError%': RangeError,
        '%ReferenceError%': ReferenceError,
        '%Reflect%': typeof Reflect === 'undefined' ? undefined : Reflect,
        '%RegExp%': RegExp,
        '%Set%': typeof Set === 'undefined' ? undefined : Set,
        '%SetIteratorPrototype%': typeof Set === 'undefined' || !hasSymbols ? undefined : getProto(new Set()[Symbol.iterator]()),
        '%SharedArrayBuffer%': typeof SharedArrayBuffer === 'undefined' ? undefined : SharedArrayBuffer,
        '%String%': String,
        '%StringIteratorPrototype%': hasSymbols ? getProto(''[Symbol.iterator]()) : undefined,
        '%Symbol%': hasSymbols ? Symbol : undefined,
        '%SyntaxError%': $SyntaxError,
        '%ThrowTypeError%': ThrowTypeError,
        '%TypedArray%': TypedArray,
        '%TypeError%': $TypeError,
        '%Uint8Array%': typeof Uint8Array === 'undefined' ? undefined : Uint8Array,
        '%Uint8ClampedArray%': typeof Uint8ClampedArray === 'undefined' ? undefined : Uint8ClampedArray,
        '%Uint16Array%': typeof Uint16Array === 'undefined' ? undefined : Uint16Array,
        '%Uint32Array%': typeof Uint32Array === 'undefined' ? undefined : Uint32Array,
        '%URIError%': URIError,
        '%WeakMap%': typeof WeakMap === 'undefined' ? undefined : WeakMap,
        '%WeakRef%': typeof WeakRef === 'undefined' ? undefined : WeakRef,
        '%WeakSet%': typeof WeakSet === 'undefined' ? undefined : WeakSet
      };

      try {
        null.error; // eslint-disable-line no-unused-expressions
      } catch (e) {
        // https://github.com/tc39/proposal-shadowrealm/pull/384#issuecomment-1364264229
        var errorProto = getProto(getProto(e));
        INTRINSICS['%Error.prototype%'] = errorProto;
      }

      var doEval = function doEval(name) {
        var value;
        if (name === '%AsyncFunction%') {
          value = getEvalledConstructor('async function () {}');
        } else if (name === '%GeneratorFunction%') {
          value = getEvalledConstructor('function* () {}');
        } else if (name === '%AsyncGeneratorFunction%') {
          value = getEvalledConstructor('async function* () {}');
        } else if (name === '%AsyncGenerator%') {
          var fn = doEval('%AsyncGeneratorFunction%');
          if (fn) {
            value = fn.prototype;
          }
        } else if (name === '%AsyncIteratorPrototype%') {
          var gen = doEval('%AsyncGenerator%');
          if (gen) {
            value = getProto(gen.prototype);
          }
        }

        INTRINSICS[name] = value;

        return value;
      };

      var LEGACY_ALIASES = {
        '%ArrayBufferPrototype%': ['ArrayBuffer', 'prototype'],
        '%ArrayPrototype%': ['Array', 'prototype'],
        '%ArrayProto_entries%': ['Array', 'prototype', 'entries'],
        '%ArrayProto_forEach%': ['Array', 'prototype', 'forEach'],
        '%ArrayProto_keys%': ['Array', 'prototype', 'keys'],
        '%ArrayProto_values%': ['Array', 'prototype', 'values'],
        '%AsyncFunctionPrototype%': ['AsyncFunction', 'prototype'],
        '%AsyncGenerator%': ['AsyncGeneratorFunction', 'prototype'],
        '%AsyncGeneratorPrototype%': ['AsyncGeneratorFunction', 'prototype', 'prototype'],
        '%BooleanPrototype%': ['Boolean', 'prototype'],
        '%DataViewPrototype%': ['DataView', 'prototype'],
        '%DatePrototype%': ['Date', 'prototype'],
        '%ErrorPrototype%': ['Error', 'prototype'],
        '%EvalErrorPrototype%': ['EvalError', 'prototype'],
        '%Float32ArrayPrototype%': ['Float32Array', 'prototype'],
        '%Float64ArrayPrototype%': ['Float64Array', 'prototype'],
        '%FunctionPrototype%': ['Function', 'prototype'],
        '%Generator%': ['GeneratorFunction', 'prototype'],
        '%GeneratorPrototype%': ['GeneratorFunction', 'prototype', 'prototype'],
        '%Int8ArrayPrototype%': ['Int8Array', 'prototype'],
        '%Int16ArrayPrototype%': ['Int16Array', 'prototype'],
        '%Int32ArrayPrototype%': ['Int32Array', 'prototype'],
        '%JSONParse%': ['JSON', 'parse'],
        '%JSONStringify%': ['JSON', 'stringify'],
        '%MapPrototype%': ['Map', 'prototype'],
        '%NumberPrototype%': ['Number', 'prototype'],
        '%ObjectPrototype%': ['Object', 'prototype'],
        '%ObjProto_toString%': ['Object', 'prototype', 'toString'],
        '%ObjProto_valueOf%': ['Object', 'prototype', 'valueOf'],
        '%PromisePrototype%': ['Promise', 'prototype'],
        '%PromiseProto_then%': ['Promise', 'prototype', 'then'],
        '%Promise_all%': ['Promise', 'all'],
        '%Promise_reject%': ['Promise', 'reject'],
        '%Promise_resolve%': ['Promise', 'resolve'],
        '%RangeErrorPrototype%': ['RangeError', 'prototype'],
        '%ReferenceErrorPrototype%': ['ReferenceError', 'prototype'],
        '%RegExpPrototype%': ['RegExp', 'prototype'],
        '%SetPrototype%': ['Set', 'prototype'],
        '%SharedArrayBufferPrototype%': ['SharedArrayBuffer', 'prototype'],
        '%StringPrototype%': ['String', 'prototype'],
        '%SymbolPrototype%': ['Symbol', 'prototype'],
        '%SyntaxErrorPrototype%': ['SyntaxError', 'prototype'],
        '%TypedArrayPrototype%': ['TypedArray', 'prototype'],
        '%TypeErrorPrototype%': ['TypeError', 'prototype'],
        '%Uint8ArrayPrototype%': ['Uint8Array', 'prototype'],
        '%Uint8ClampedArrayPrototype%': ['Uint8ClampedArray', 'prototype'],
        '%Uint16ArrayPrototype%': ['Uint16Array', 'prototype'],
        '%Uint32ArrayPrototype%': ['Uint32Array', 'prototype'],
        '%URIErrorPrototype%': ['URIError', 'prototype'],
        '%WeakMapPrototype%': ['WeakMap', 'prototype'],
        '%WeakSetPrototype%': ['WeakSet', 'prototype']
      };

      var bind = require('function-bind');
      var hasOwn = require('has');
      var $concat = bind.call(Function.call, Array.prototype.concat);
      var $spliceApply = bind.call(Function.apply, Array.prototype.splice);
      var $replace = bind.call(Function.call, String.prototype.replace);
      var $strSlice = bind.call(Function.call, String.prototype.slice);
      var $exec = bind.call(Function.call, RegExp.prototype.exec);

      /* adapted from https://github.com/lodash/lodash/blob/4.17.15/dist/lodash.js#L6735-L6744 */
      var rePropName = /[^%.[\]]+|\[(?:(-?\d+(?:\.\d+)?)|(["'])((?:(?!\2)[^\\]|\\.)*?)\2)\]|(?=(?:\.|\[\])(?:\.|\[\]|%$))/g;
      var reEscapeChar = /\\(\\)?/g; /** Used to match backslashes in property paths. */
      var stringToPath = function stringToPath(string) {
        var first = $strSlice(string, 0, 1);
        var last = $strSlice(string, -1);
        if (first === '%' && last !== '%') {
          throw new $SyntaxError('invalid intrinsic syntax, expected closing `%`');
        } else if (last === '%' && first !== '%') {
          throw new $SyntaxError('invalid intrinsic syntax, expected opening `%`');
        }
        var result = [];
        $replace(string, rePropName, function (match, number, quote, subString) {
          result[result.length] = quote ? $replace(subString, reEscapeChar, '$1') : number || match;
        });
        return result;
      };
      /* end adaptation */

      var getBaseIntrinsic = function getBaseIntrinsic(name, allowMissing) {
        var intrinsicName = name;
        var alias;
        if (hasOwn(LEGACY_ALIASES, intrinsicName)) {
          alias = LEGACY_ALIASES[intrinsicName];
          intrinsicName = '%' + alias[0] + '%';
        }

        if (hasOwn(INTRINSICS, intrinsicName)) {
          var value = INTRINSICS[intrinsicName];
          if (value === needsEval) {
            value = doEval(intrinsicName);
          }
          if (typeof value === 'undefined' && !allowMissing) {
            throw new $TypeError('intrinsic ' + name + ' exists, but is not available. Please file an issue!');
          }

          return {
            alias: alias,
            name: intrinsicName,
            value: value
          };
        }

        throw new $SyntaxError('intrinsic ' + name + ' does not exist!');
      };

      module.exports = function GetIntrinsic(name, allowMissing) {
        if (typeof name !== 'string' || name.length === 0) {
          throw new $TypeError('intrinsic name must be a non-empty string');
        }
        if (arguments.length > 1 && typeof allowMissing !== 'boolean') {
          throw new $TypeError('"allowMissing" argument must be a boolean');
        }

        if ($exec(/^%?[^%]*%?$/, name) === null) {
          throw new $SyntaxError('`%` may not be present anywhere but at the beginning and end of the intrinsic name');
        }
        var parts = stringToPath(name);
        var intrinsicBaseName = parts.length > 0 ? parts[0] : '';

        var intrinsic = getBaseIntrinsic('%' + intrinsicBaseName + '%', allowMissing);
        var intrinsicRealName = intrinsic.name;
        var value = intrinsic.value;
        var skipFurtherCaching = false;

        var alias = intrinsic.alias;
        if (alias) {
          intrinsicBaseName = alias[0];
          $spliceApply(parts, $concat([0, 1], alias));
        }

        for (var i = 1, isOwn = true; i < parts.length; i += 1) {
          var part = parts[i];
          var first = $strSlice(part, 0, 1);
          var last = $strSlice(part, -1);
          if (
            (
              (first === '"' || first === "'" || first === '`')
              || (last === '"' || last === "'" || last === '`')
            )
            && first !== last
          ) {
            throw new $SyntaxError('property names with quotes must have matching quotes');
          }
          if (part === 'constructor' || !isOwn) {
            skipFurtherCaching = true;
          }

          intrinsicBaseName += '.' + part;
          intrinsicRealName = '%' + intrinsicBaseName + '%';

          if (hasOwn(INTRINSICS, intrinsicRealName)) {
            value = INTRINSICS[intrinsicRealName];
          } else if (value != null) {
            if (!(part in value)) {
              if (!allowMissing) {
                throw new $TypeError('base intrinsic for ' + name + ' exists, but the property is not available.');
              }
              return void undefined;
            }
            if ($gOPD && (i + 1) >= parts.length) {
              var desc = $gOPD(value, part);
              isOwn = !!desc;

              // By convention, when a data property is converted to an accessor
              // property to emulate a data property that does not suffer from
              // the override mistake, that accessor's getter is marked with
              // an `originalValue` property. Here, when we detect this, we
              // uphold the illusion by pretending to see that original data
              // property, i.e., returning the value rather than the getter
              // itself.
              if (isOwn && 'get' in desc && !('originalValue' in desc.get)) {
                value = desc.get;
              } else {
                value = value[part];
              }
            } else {
              isOwn = hasOwn(value, part);
              value = value[part];
            }

            if (isOwn && !skipFurtherCaching) {
              INTRINSICS[intrinsicRealName] = value;
            }
          }
        }
        return value;
      };

    }, { "function-bind": 7, "has": 13, "has-symbols": 10 }], 9: [function (require, module, exports) {
      'use strict';

      var GetIntrinsic = require('get-intrinsic');

      var $gOPD = GetIntrinsic('%Object.getOwnPropertyDescriptor%', true);

      if ($gOPD) {
        try {
          $gOPD([], 'length');
        } catch (e) {
          // IE 8 has a broken gOPD
          $gOPD = null;
        }
      }

      module.exports = $gOPD;

    }, { "get-intrinsic": 8 }], 10: [function (require, module, exports) {
      'use strict';

      var origSymbol = typeof Symbol !== 'undefined' && Symbol;
      var hasSymbolSham = require('./shams');

      module.exports = function hasNativeSymbols() {
        if (typeof origSymbol !== 'function') { return false; }
        if (typeof Symbol !== 'function') { return false; }
        if (typeof origSymbol('foo') !== 'symbol') { return false; }
        if (typeof Symbol('bar') !== 'symbol') { return false; }

        return hasSymbolSham();
      };

    }, { "./shams": 11 }], 11: [function (require, module, exports) {
      'use strict';

      /* eslint complexity: [2, 18], max-statements: [2, 33] */
      module.exports = function hasSymbols() {
        if (typeof Symbol !== 'function' || typeof Object.getOwnPropertySymbols !== 'function') { return false; }
        if (typeof Symbol.iterator === 'symbol') { return true; }

        var obj = {};
        var sym = Symbol('test');
        var symObj = Object(sym);
        if (typeof sym === 'string') { return false; }

        if (Object.prototype.toString.call(sym) !== '[object Symbol]') { return false; }
        if (Object.prototype.toString.call(symObj) !== '[object Symbol]') { return false; }

        // temp disabled per https://github.com/ljharb/object.assign/issues/17
        // if (sym instanceof Symbol) { return false; }
        // temp disabled per https://github.com/WebReflection/get-own-property-symbols/issues/4
        // if (!(symObj instanceof Symbol)) { return false; }

        // if (typeof Symbol.prototype.toString !== 'function') { return false; }
        // if (String(sym) !== Symbol.prototype.toString.call(sym)) { return false; }

        var symVal = 42;
        obj[sym] = symVal;
        for (sym in obj) { return false; } // eslint-disable-line no-restricted-syntax, no-unreachable-loop
        if (typeof Object.keys === 'function' && Object.keys(obj).length !== 0) { return false; }

        if (typeof Object.getOwnPropertyNames === 'function' && Object.getOwnPropertyNames(obj).length !== 0) { return false; }

        var syms = Object.getOwnPropertySymbols(obj);
        if (syms.length !== 1 || syms[0] !== sym) { return false; }

        if (!Object.prototype.propertyIsEnumerable.call(obj, sym)) { return false; }

        if (typeof Object.getOwnPropertyDescriptor === 'function') {
          var descriptor = Object.getOwnPropertyDescriptor(obj, sym);
          if (descriptor.value !== symVal || descriptor.enumerable !== true) { return false; }
        }

        return true;
      };

    }, {}], 12: [function (require, module, exports) {
      'use strict';

      var hasSymbols = require('has-symbols/shams');

      module.exports = function hasToStringTagShams() {
        return hasSymbols() && !!Symbol.toStringTag;
      };

    }, { "has-symbols/shams": 11 }], 13: [function (require, module, exports) {
      'use strict';

      var bind = require('function-bind');

      module.exports = bind.call(Function.call, Object.prototype.hasOwnProperty);

    }, { "function-bind": 7 }], 14: [function (require, module, exports) {
      if (typeof Object.create === 'function') {
        // implementation from standard node.js 'util' module
        module.exports = function inherits(ctor, superCtor) {
          if (superCtor) {
            ctor.super_ = superCtor
            ctor.prototype = Object.create(superCtor.prototype, {
              constructor: {
                value: ctor,
                enumerable: false,
                writable: true,
                configurable: true
              }
            })
          }
        };
      } else {
        // old school shim for old browsers
        module.exports = function inherits(ctor, superCtor) {
          if (superCtor) {
            ctor.super_ = superCtor
            var TempCtor = function () { }
            TempCtor.prototype = superCtor.prototype
            ctor.prototype = new TempCtor()
            ctor.prototype.constructor = ctor
          }
        }
      }

    }, {}], 15: [function (require, module, exports) {
      'use strict';

      var hasToStringTag = require('has-tostringtag/shams')();
      var callBound = require('call-bind/callBound');

      var $toString = callBound('Object.prototype.toString');

      var isStandardArguments = function isArguments(value) {
        if (hasToStringTag && value && typeof value === 'object' && Symbol.toStringTag in value) {
          return false;
        }
        return $toString(value) === '[object Arguments]';
      };

      var isLegacyArguments = function isArguments(value) {
        if (isStandardArguments(value)) {
          return true;
        }
        return value !== null &&
          typeof value === 'object' &&
          typeof value.length === 'number' &&
          value.length >= 0 &&
          $toString(value) !== '[object Array]' &&
          $toString(value.callee) === '[object Function]';
      };

      var supportsStandardArguments = (function () {
        return isStandardArguments(arguments);
      }());

      isStandardArguments.isLegacyArguments = isLegacyArguments; // for tests

      module.exports = supportsStandardArguments ? isStandardArguments : isLegacyArguments;

    }, { "call-bind/callBound": 3, "has-tostringtag/shams": 12 }], 16: [function (require, module, exports) {
      'use strict';

      var fnToStr = Function.prototype.toString;
      var reflectApply = typeof Reflect === 'object' && Reflect !== null && Reflect.apply;
      var badArrayLike;
      var isCallableMarker;
      if (typeof reflectApply === 'function' && typeof Object.defineProperty === 'function') {
        try {
          badArrayLike = Object.defineProperty({}, 'length', {
            get: function () {
              throw isCallableMarker;
            }
          });
          isCallableMarker = {};
          // eslint-disable-next-line no-throw-literal
          reflectApply(function () { throw 42; }, null, badArrayLike);
        } catch (_) {
          if (_ !== isCallableMarker) {
            reflectApply = null;
          }
        }
      } else {
        reflectApply = null;
      }

      var constructorRegex = /^\s*class\b/;
      var isES6ClassFn = function isES6ClassFunction(value) {
        try {
          var fnStr = fnToStr.call(value);
          return constructorRegex.test(fnStr);
        } catch (e) {
          return false; // not a function
        }
      };

      var tryFunctionObject = function tryFunctionToStr(value) {
        try {
          if (isES6ClassFn(value)) { return false; }
          fnToStr.call(value);
          return true;
        } catch (e) {
          return false;
        }
      };
      var toStr = Object.prototype.toString;
      var objectClass = '[object Object]';
      var fnClass = '[object Function]';
      var genClass = '[object GeneratorFunction]';
      var ddaClass = '[object HTMLAllCollection]'; // IE 11
      var ddaClass2 = '[object HTML document.all class]';
      var ddaClass3 = '[object HTMLCollection]'; // IE 9-10
      var hasToStringTag = typeof Symbol === 'function' && !!Symbol.toStringTag; // better: use `has-tostringtag`

      var isIE68 = !(0 in [,]); // eslint-disable-line no-sparse-arrays, comma-spacing

      var isDDA = function isDocumentDotAll() { return false; };
      if (typeof document === 'object') {
        // Firefox 3 canonicalizes DDA to undefined when it's not accessed directly
        var all = document.all;
        if (toStr.call(all) === toStr.call(document.all)) {
          isDDA = function isDocumentDotAll(value) {
            /* globals document: false */
            // in IE 6-8, typeof document.all is "object" and it's truthy
            if ((isIE68 || !value) && (typeof value === 'undefined' || typeof value === 'object')) {
              try {
                var str = toStr.call(value);
                return (
                  str === ddaClass
                  || str === ddaClass2
                  || str === ddaClass3 // opera 12.16
                  || str === objectClass // IE 6-8
                ) && value('') == null; // eslint-disable-line eqeqeq
              } catch (e) { /**/ }
            }
            return false;
          };
        }
      }

      module.exports = reflectApply
        ? function isCallable(value) {
          if (isDDA(value)) { return true; }
          if (!value) { return false; }
          if (typeof value !== 'function' && typeof value !== 'object') { return false; }
          try {
            reflectApply(value, null, badArrayLike);
          } catch (e) {
            if (e !== isCallableMarker) { return false; }
          }
          return !isES6ClassFn(value) && tryFunctionObject(value);
        }
        : function isCallable(value) {
          if (isDDA(value)) { return true; }
          if (!value) { return false; }
          if (typeof value !== 'function' && typeof value !== 'object') { return false; }
          if (hasToStringTag) { return tryFunctionObject(value); }
          if (isES6ClassFn(value)) { return false; }
          var strClass = toStr.call(value);
          if (strClass !== fnClass && strClass !== genClass && !(/^\[object HTML/).test(strClass)) { return false; }
          return tryFunctionObject(value);
        };

    }, {}], 17: [function (require, module, exports) {
      'use strict';

      var toStr = Object.prototype.toString;
      var fnToStr = Function.prototype.toString;
      var isFnRegex = /^\s*(?:function)?\*/;
      var hasToStringTag = require('has-tostringtag/shams')();
      var getProto = Object.getPrototypeOf;
      var getGeneratorFunc = function () { // eslint-disable-line consistent-return
        if (!hasToStringTag) {
          return false;
        }
        try {
          return Function('return function*() {}')();
        } catch (e) {
        }
      };
      var GeneratorFunction;

      module.exports = function isGeneratorFunction(fn) {
        if (typeof fn !== 'function') {
          return false;
        }
        if (isFnRegex.test(fnToStr.call(fn))) {
          return true;
        }
        if (!hasToStringTag) {
          var str = toStr.call(fn);
          return str === '[object GeneratorFunction]';
        }
        if (!getProto) {
          return false;
        }
        if (typeof GeneratorFunction === 'undefined') {
          var generatorFunc = getGeneratorFunc();
          GeneratorFunction = generatorFunc ? getProto(generatorFunc) : false;
        }
        return getProto(fn) === GeneratorFunction;
      };

    }, { "has-tostringtag/shams": 12 }], 18: [function (require, module, exports) {
      (function (global) {
        (function () {
          'use strict';

          var forEach = require('for-each');
          var availableTypedArrays = require('available-typed-arrays');
          var callBound = require('call-bind/callBound');

          var $toString = callBound('Object.prototype.toString');
          var hasToStringTag = require('has-tostringtag/shams')();
          var gOPD = require('gopd');

          var g = typeof globalThis === 'undefined' ? global : globalThis;
          var typedArrays = availableTypedArrays();

          var $indexOf = callBound('Array.prototype.indexOf', true) || function indexOf(array, value) {
            for (var i = 0; i < array.length; i += 1) {
              if (array[i] === value) {
                return i;
              }
            }
            return -1;
          };
          var $slice = callBound('String.prototype.slice');
          var toStrTags = {};
          var getPrototypeOf = Object.getPrototypeOf; // require('getprototypeof');
          if (hasToStringTag && gOPD && getPrototypeOf) {
            forEach(typedArrays, function (typedArray) {
              var arr = new g[typedArray]();
              if (Symbol.toStringTag in arr) {
                var proto = getPrototypeOf(arr);
                var descriptor = gOPD(proto, Symbol.toStringTag);
                if (!descriptor) {
                  var superProto = getPrototypeOf(proto);
                  descriptor = gOPD(superProto, Symbol.toStringTag);
                }
                toStrTags[typedArray] = descriptor.get;
              }
            });
          }

          var tryTypedArrays = function tryAllTypedArrays(value) {
            var anyTrue = false;
            forEach(toStrTags, function (getter, typedArray) {
              if (!anyTrue) {
                try {
                  anyTrue = getter.call(value) === typedArray;
                } catch (e) { /**/ }
              }
            });
            return anyTrue;
          };

          module.exports = function isTypedArray(value) {
            if (!value || typeof value !== 'object') { return false; }
            if (!hasToStringTag || !(Symbol.toStringTag in value)) {
              var tag = $slice($toString(value), 8, -1);
              return $indexOf(typedArrays, tag) > -1;
            }
            if (!gOPD) { return false; }
            return tryTypedArrays(value);
          };

        }).call(this)
      }).call(this, typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})
    }, { "available-typed-arrays": 2, "call-bind/callBound": 3, "for-each": 5, "gopd": 9, "has-tostringtag/shams": 12 }], 19: [function (require, module, exports) {
      // shim for using process in browser
      var process = module.exports = {};

      // cached from whatever global is present so that test runners that stub it
      // don't break things.  But we need to wrap it in a try catch in case it is
      // wrapped in strict mode code which doesn't define any globals.  It's inside a
      // function because try/catches deoptimize in certain engines.

      var cachedSetTimeout;
      var cachedClearTimeout;

      function defaultSetTimout() {
        throw new Error('setTimeout has not been defined');
      }
      function defaultClearTimeout() {
        throw new Error('clearTimeout has not been defined');
      }
      (function () {
        try {
          if (typeof setTimeout === 'function') {
            cachedSetTimeout = setTimeout;
          } else {
            cachedSetTimeout = defaultSetTimout;
          }
        } catch (e) {
          cachedSetTimeout = defaultSetTimout;
        }
        try {
          if (typeof clearTimeout === 'function') {
            cachedClearTimeout = clearTimeout;
          } else {
            cachedClearTimeout = defaultClearTimeout;
          }
        } catch (e) {
          cachedClearTimeout = defaultClearTimeout;
        }
      }())
      function runTimeout(fun) {
        if (cachedSetTimeout === setTimeout) {
          //normal enviroments in sane situations
          return setTimeout(fun, 0);
        }
        // if setTimeout wasn't available but was latter defined
        if ((cachedSetTimeout === defaultSetTimout || !cachedSetTimeout) && setTimeout) {
          cachedSetTimeout = setTimeout;
          return setTimeout(fun, 0);
        }
        try {
          // when when somebody has screwed with setTimeout but no I.E. maddness
          return cachedSetTimeout(fun, 0);
        } catch (e) {
          try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't trust the global object when called normally
            return cachedSetTimeout.call(null, fun, 0);
          } catch (e) {
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error
            return cachedSetTimeout.call(this, fun, 0);
          }
        }


      }
      function runClearTimeout(marker) {
        if (cachedClearTimeout === clearTimeout) {
          //normal enviroments in sane situations
          return clearTimeout(marker);
        }
        // if clearTimeout wasn't available but was latter defined
        if ((cachedClearTimeout === defaultClearTimeout || !cachedClearTimeout) && clearTimeout) {
          cachedClearTimeout = clearTimeout;
          return clearTimeout(marker);
        }
        try {
          // when when somebody has screwed with setTimeout but no I.E. maddness
          return cachedClearTimeout(marker);
        } catch (e) {
          try {
            // When we are in I.E. but the script has been evaled so I.E. doesn't  trust the global object when called normally
            return cachedClearTimeout.call(null, marker);
          } catch (e) {
            // same as above but when it's a version of I.E. that must have the global object for 'this', hopfully our context correct otherwise it will throw a global error.
            // Some versions of I.E. have different rules for clearTimeout vs setTimeout
            return cachedClearTimeout.call(this, marker);
          }
        }



      }
      var queue = [];
      var draining = false;
      var currentQueue;
      var queueIndex = -1;

      function cleanUpNextTick() {
        if (!draining || !currentQueue) {
          return;
        }
        draining = false;
        if (currentQueue.length) {
          queue = currentQueue.concat(queue);
        } else {
          queueIndex = -1;
        }
        if (queue.length) {
          drainQueue();
        }
      }

      function drainQueue() {
        if (draining) {
          return;
        }
        var timeout = runTimeout(cleanUpNextTick);
        draining = true;

        var len = queue.length;
        while (len) {
          currentQueue = queue;
          queue = [];
          while (++queueIndex < len) {
            if (currentQueue) {
              currentQueue[queueIndex].run();
            }
          }
          queueIndex = -1;
          len = queue.length;
        }
        currentQueue = null;
        draining = false;
        runClearTimeout(timeout);
      }

      process.nextTick = function (fun) {
        var args = new Array(arguments.length - 1);
        if (arguments.length > 1) {
          for (var i = 1; i < arguments.length; i++) {
            args[i - 1] = arguments[i];
          }
        }
        queue.push(new Item(fun, args));
        if (queue.length === 1 && !draining) {
          runTimeout(drainQueue);
        }
      };

      // v8 likes predictible objects
      function Item(fun, array) {
        this.fun = fun;
        this.array = array;
      }
      Item.prototype.run = function () {
        this.fun.apply(null, this.array);
      };
      process.title = 'browser';
      process.browser = true;
      process.env = {};
      process.argv = [];
      process.version = ''; // empty string to avoid regexp issues
      process.versions = {};

      function noop() { }

      process.on = noop;
      process.addListener = noop;
      process.once = noop;
      process.off = noop;
      process.removeListener = noop;
      process.removeAllListeners = noop;
      process.emit = noop;
      process.prependListener = noop;
      process.prependOnceListener = noop;

      process.listeners = function (name) { return [] }

      process.binding = function (name) {
        throw new Error('process.binding is not supported');
      };

      process.cwd = function () { return '/' };
      process.chdir = function (dir) {
        throw new Error('process.chdir is not supported');
      };
      process.umask = function () { return 0; };

    }, {}], 20: [function (require, module, exports) {
      module.exports = function isBuffer(arg) {
        return arg && typeof arg === 'object'
          && typeof arg.copy === 'function'
          && typeof arg.fill === 'function'
          && typeof arg.readUInt8 === 'function';
      }
    }, {}], 21: [function (require, module, exports) {
      // Currently in sync with Node.js lib/internal/util/types.js
      // https://github.com/nodejs/node/commit/112cc7c27551254aa2b17098fb774867f05ed0d9

      'use strict';

      var isArgumentsObject = require('is-arguments');
      var isGeneratorFunction = require('is-generator-function');
      var whichTypedArray = require('which-typed-array');
      var isTypedArray = require('is-typed-array');

      function uncurryThis(f) {
        return f.call.bind(f);
      }

      var BigIntSupported = typeof BigInt !== 'undefined';
      var SymbolSupported = typeof Symbol !== 'undefined';

      var ObjectToString = uncurryThis(Object.prototype.toString);

      var numberValue = uncurryThis(Number.prototype.valueOf);
      var stringValue = uncurryThis(String.prototype.valueOf);
      var booleanValue = uncurryThis(Boolean.prototype.valueOf);

      if (BigIntSupported) {
        var bigIntValue = uncurryThis(BigInt.prototype.valueOf);
      }

      if (SymbolSupported) {
        var symbolValue = uncurryThis(Symbol.prototype.valueOf);
      }

      function checkBoxedPrimitive(value, prototypeValueOf) {
        if (typeof value !== 'object') {
          return false;
        }
        try {
          prototypeValueOf(value);
          return true;
        } catch (e) {
          return false;
        }
      }

      exports.isArgumentsObject = isArgumentsObject;
      exports.isGeneratorFunction = isGeneratorFunction;
      exports.isTypedArray = isTypedArray;

      // Taken from here and modified for better browser support
      // https://github.com/sindresorhus/p-is-promise/blob/cda35a513bda03f977ad5cde3a079d237e82d7ef/index.js
      function isPromise(input) {
        return (
          (
            typeof Promise !== 'undefined' &&
            input instanceof Promise
          ) ||
          (
            input !== null &&
            typeof input === 'object' &&
            typeof input.then === 'function' &&
            typeof input.catch === 'function'
          )
        );
      }
      exports.isPromise = isPromise;

      function isArrayBufferView(value) {
        if (typeof ArrayBuffer !== 'undefined' && ArrayBuffer.isView) {
          return ArrayBuffer.isView(value);
        }

        return (
          isTypedArray(value) ||
          isDataView(value)
        );
      }
      exports.isArrayBufferView = isArrayBufferView;


      function isUint8Array(value) {
        return whichTypedArray(value) === 'Uint8Array';
      }
      exports.isUint8Array = isUint8Array;

      function isUint8ClampedArray(value) {
        return whichTypedArray(value) === 'Uint8ClampedArray';
      }
      exports.isUint8ClampedArray = isUint8ClampedArray;

      function isUint16Array(value) {
        return whichTypedArray(value) === 'Uint16Array';
      }
      exports.isUint16Array = isUint16Array;

      function isUint32Array(value) {
        return whichTypedArray(value) === 'Uint32Array';
      }
      exports.isUint32Array = isUint32Array;

      function isInt8Array(value) {
        return whichTypedArray(value) === 'Int8Array';
      }
      exports.isInt8Array = isInt8Array;

      function isInt16Array(value) {
        return whichTypedArray(value) === 'Int16Array';
      }
      exports.isInt16Array = isInt16Array;

      function isInt32Array(value) {
        return whichTypedArray(value) === 'Int32Array';
      }
      exports.isInt32Array = isInt32Array;

      function isFloat32Array(value) {
        return whichTypedArray(value) === 'Float32Array';
      }
      exports.isFloat32Array = isFloat32Array;

      function isFloat64Array(value) {
        return whichTypedArray(value) === 'Float64Array';
      }
      exports.isFloat64Array = isFloat64Array;

      function isBigInt64Array(value) {
        return whichTypedArray(value) === 'BigInt64Array';
      }
      exports.isBigInt64Array = isBigInt64Array;

      function isBigUint64Array(value) {
        return whichTypedArray(value) === 'BigUint64Array';
      }
      exports.isBigUint64Array = isBigUint64Array;

      function isMapToString(value) {
        return ObjectToString(value) === '[object Map]';
      }
      isMapToString.working = (
        typeof Map !== 'undefined' &&
        isMapToString(new Map())
      );

      function isMap(value) {
        if (typeof Map === 'undefined') {
          return false;
        }

        return isMapToString.working
          ? isMapToString(value)
          : value instanceof Map;
      }
      exports.isMap = isMap;

      function isSetToString(value) {
        return ObjectToString(value) === '[object Set]';
      }
      isSetToString.working = (
        typeof Set !== 'undefined' &&
        isSetToString(new Set())
      );
      function isSet(value) {
        if (typeof Set === 'undefined') {
          return false;
        }

        return isSetToString.working
          ? isSetToString(value)
          : value instanceof Set;
      }
      exports.isSet = isSet;

      function isWeakMapToString(value) {
        return ObjectToString(value) === '[object WeakMap]';
      }
      isWeakMapToString.working = (
        typeof WeakMap !== 'undefined' &&
        isWeakMapToString(new WeakMap())
      );
      function isWeakMap(value) {
        if (typeof WeakMap === 'undefined') {
          return false;
        }

        return isWeakMapToString.working
          ? isWeakMapToString(value)
          : value instanceof WeakMap;
      }
      exports.isWeakMap = isWeakMap;

      function isWeakSetToString(value) {
        return ObjectToString(value) === '[object WeakSet]';
      }
      isWeakSetToString.working = (
        typeof WeakSet !== 'undefined' &&
        isWeakSetToString(new WeakSet())
      );
      function isWeakSet(value) {
        return isWeakSetToString(value);
      }
      exports.isWeakSet = isWeakSet;

      function isArrayBufferToString(value) {
        return ObjectToString(value) === '[object ArrayBuffer]';
      }
      isArrayBufferToString.working = (
        typeof ArrayBuffer !== 'undefined' &&
        isArrayBufferToString(new ArrayBuffer())
      );
      function isArrayBuffer(value) {
        if (typeof ArrayBuffer === 'undefined') {
          return false;
        }

        return isArrayBufferToString.working
          ? isArrayBufferToString(value)
          : value instanceof ArrayBuffer;
      }
      exports.isArrayBuffer = isArrayBuffer;

      function isDataViewToString(value) {
        return ObjectToString(value) === '[object DataView]';
      }
      isDataViewToString.working = (
        typeof ArrayBuffer !== 'undefined' &&
        typeof DataView !== 'undefined' &&
        isDataViewToString(new DataView(new ArrayBuffer(1), 0, 1))
      );
      function isDataView(value) {
        if (typeof DataView === 'undefined') {
          return false;
        }

        return isDataViewToString.working
          ? isDataViewToString(value)
          : value instanceof DataView;
      }
      exports.isDataView = isDataView;

      // Store a copy of SharedArrayBuffer in case it's deleted elsewhere
      var SharedArrayBufferCopy = typeof SharedArrayBuffer !== 'undefined' ? SharedArrayBuffer : undefined;
      function isSharedArrayBufferToString(value) {
        return ObjectToString(value) === '[object SharedArrayBuffer]';
      }
      function isSharedArrayBuffer(value) {
        if (typeof SharedArrayBufferCopy === 'undefined') {
          return false;
        }

        if (typeof isSharedArrayBufferToString.working === 'undefined') {
          isSharedArrayBufferToString.working = isSharedArrayBufferToString(new SharedArrayBufferCopy());
        }

        return isSharedArrayBufferToString.working
          ? isSharedArrayBufferToString(value)
          : value instanceof SharedArrayBufferCopy;
      }
      exports.isSharedArrayBuffer = isSharedArrayBuffer;

      function isAsyncFunction(value) {
        return ObjectToString(value) === '[object AsyncFunction]';
      }
      exports.isAsyncFunction = isAsyncFunction;

      function isMapIterator(value) {
        return ObjectToString(value) === '[object Map Iterator]';
      }
      exports.isMapIterator = isMapIterator;

      function isSetIterator(value) {
        return ObjectToString(value) === '[object Set Iterator]';
      }
      exports.isSetIterator = isSetIterator;

      function isGeneratorObject(value) {
        return ObjectToString(value) === '[object Generator]';
      }
      exports.isGeneratorObject = isGeneratorObject;

      function isWebAssemblyCompiledModule(value) {
        return ObjectToString(value) === '[object WebAssembly.Module]';
      }
      exports.isWebAssemblyCompiledModule = isWebAssemblyCompiledModule;

      function isNumberObject(value) {
        return checkBoxedPrimitive(value, numberValue);
      }
      exports.isNumberObject = isNumberObject;

      function isStringObject(value) {
        return checkBoxedPrimitive(value, stringValue);
      }
      exports.isStringObject = isStringObject;

      function isBooleanObject(value) {
        return checkBoxedPrimitive(value, booleanValue);
      }
      exports.isBooleanObject = isBooleanObject;

      function isBigIntObject(value) {
        return BigIntSupported && checkBoxedPrimitive(value, bigIntValue);
      }
      exports.isBigIntObject = isBigIntObject;

      function isSymbolObject(value) {
        return SymbolSupported && checkBoxedPrimitive(value, symbolValue);
      }
      exports.isSymbolObject = isSymbolObject;

      function isBoxedPrimitive(value) {
        return (
          isNumberObject(value) ||
          isStringObject(value) ||
          isBooleanObject(value) ||
          isBigIntObject(value) ||
          isSymbolObject(value)
        );
      }
      exports.isBoxedPrimitive = isBoxedPrimitive;

      function isAnyArrayBuffer(value) {
        return typeof Uint8Array !== 'undefined' && (
          isArrayBuffer(value) ||
          isSharedArrayBuffer(value)
        );
      }
      exports.isAnyArrayBuffer = isAnyArrayBuffer;

      ['isProxy', 'isExternal', 'isModuleNamespaceObject'].forEach(function (method) {
        Object.defineProperty(exports, method, {
          enumerable: false,
          value: function () {
            throw new Error(method + ' is not supported in userland');
          }
        });
      });

    }, { "is-arguments": 15, "is-generator-function": 17, "is-typed-array": 18, "which-typed-array": 23 }], 22: [function (require, module, exports) {
      (function (process) {
        (function () {
          // Copyright Joyent, Inc. and other Node contributors.
          //
          // Permission is hereby granted, free of charge, to any person obtaining a
          // copy of this software and associated documentation files (the
          // "Software"), to deal in the Software without restriction, including
          // without limitation the rights to use, copy, modify, merge, publish,
          // distribute, sublicense, and/or sell copies of the Software, and to permit
          // persons to whom the Software is furnished to do so, subject to the
          // following conditions:
          //
          // The above copyright notice and this permission notice shall be included
          // in all copies or substantial portions of the Software.
          //
          // THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
          // OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
          // MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
          // NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
          // DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
          // OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
          // USE OR OTHER DEALINGS IN THE SOFTWARE.

          var getOwnPropertyDescriptors = Object.getOwnPropertyDescriptors ||
            function getOwnPropertyDescriptors(obj) {
              var keys = Object.keys(obj);
              var descriptors = {};
              for (var i = 0; i < keys.length; i++) {
                descriptors[keys[i]] = Object.getOwnPropertyDescriptor(obj, keys[i]);
              }
              return descriptors;
            };

          var formatRegExp = /%[sdj%]/g;
          exports.format = function (f) {
            if (!isString(f)) {
              var objects = [];
              for (var i = 0; i < arguments.length; i++) {
                objects.push(inspect(arguments[i]));
              }
              return objects.join(' ');
            }

            var i = 1;
            var args = arguments;
            var len = args.length;
            var str = String(f).replace(formatRegExp, function (x) {
              if (x === '%%') return '%';
              if (i >= len) return x;
              switch (x) {
                case '%s': return String(args[i++]);
                case '%d': return Number(args[i++]);
                case '%j':
                  try {
                    return JSON.stringify(args[i++]);
                  } catch (_) {
                    return '[Circular]';
                  }
                default:
                  return x;
              }
            });
            for (var x = args[i]; i < len; x = args[++i]) {
              if (isNull(x) || !isObject(x)) {
                str += ' ' + x;
              } else {
                str += ' ' + inspect(x);
              }
            }
            return str;
          };


          // Mark that a method should not be used.
          // Returns a modified function which warns once by default.
          // If --no-deprecation is set, then it is a no-op.
          exports.deprecate = function (fn, msg) {
            if (typeof process !== 'undefined' && process.noDeprecation === true) {
              return fn;
            }

            // Allow for deprecating things in the process of starting up.
            if (typeof process === 'undefined') {
              return function () {
                return exports.deprecate(fn, msg).apply(this, arguments);
              };
            }

            var warned = false;
            function deprecated() {
              if (!warned) {
                if (process.throwDeprecation) {
                  throw new Error(msg);
                } else if (process.traceDeprecation) {
                  console.trace(msg);
                } else {
                  console.error(msg);
                }
                warned = true;
              }
              return fn.apply(this, arguments);
            }

            return deprecated;
          };


          var debugs = {};
          var debugEnvRegex = /^$/;

          if (process.env.NODE_DEBUG) {
            var debugEnv = process.env.NODE_DEBUG;
            debugEnv = debugEnv.replace(/[|\\{}()[\]^$+?.]/g, '\\$&')
              .replace(/\*/g, '.*')
              .replace(/,/g, '$|^')
              .toUpperCase();
            debugEnvRegex = new RegExp('^' + debugEnv + '$', 'i');
          }
          exports.debuglog = function (set) {
            set = set.toUpperCase();
            if (!debugs[set]) {
              if (debugEnvRegex.test(set)) {
                var pid = process.pid;
                debugs[set] = function () {
                  var msg = exports.format.apply(exports, arguments);
                  console.error('%s %d: %s', set, pid, msg);
                };
              } else {
                debugs[set] = function () { };
              }
            }
            return debugs[set];
          };


          /**
           * Echos the value of a value. Trys to print the value out
           * in the best way possible given the different types.
           *
           * @param {Object} obj The object to print out.
           * @param {Object} opts Optional options object that alters the output.
           */
          /* legacy: obj, showHidden, depth, colors*/
          function inspect(obj, opts) {
            // default options
            var ctx = {
              seen: [],
              stylize: stylizeNoColor
            };
            // legacy...
            if (arguments.length >= 3) ctx.depth = arguments[2];
            if (arguments.length >= 4) ctx.colors = arguments[3];
            if (isBoolean(opts)) {
              // legacy...
              ctx.showHidden = opts;
            } else if (opts) {
              // got an "options" object
              exports._extend(ctx, opts);
            }
            // set default options
            if (isUndefined(ctx.showHidden)) ctx.showHidden = false;
            if (isUndefined(ctx.depth)) ctx.depth = 2;
            if (isUndefined(ctx.colors)) ctx.colors = false;
            if (isUndefined(ctx.customInspect)) ctx.customInspect = true;
            if (ctx.colors) ctx.stylize = stylizeWithColor;
            return formatValue(ctx, obj, ctx.depth);
          }
          exports.inspect = inspect;


          // http://en.wikipedia.org/wiki/ANSI_escape_code#graphics
          inspect.colors = {
            'bold': [1, 22],
            'italic': [3, 23],
            'underline': [4, 24],
            'inverse': [7, 27],
            'white': [37, 39],
            'grey': [90, 39],
            'black': [30, 39],
            'blue': [34, 39],
            'cyan': [36, 39],
            'green': [32, 39],
            'magenta': [35, 39],
            'red': [31, 39],
            'yellow': [33, 39]
          };

          // Don't use 'blue' not visible on cmd.exe
          inspect.styles = {
            'special': 'cyan',
            'number': 'yellow',
            'boolean': 'yellow',
            'undefined': 'grey',
            'null': 'bold',
            'string': 'green',
            'date': 'magenta',
            // "name": intentionally not styling
            'regexp': 'red'
          };


          function stylizeWithColor(str, styleType) {
            var style = inspect.styles[styleType];

            if (style) {
              return '\u001b[' + inspect.colors[style][0] + 'm' + str +
                '\u001b[' + inspect.colors[style][1] + 'm';
            } else {
              return str;
            }
          }


          function stylizeNoColor(str, styleType) {
            return str;
          }


          function arrayToHash(array) {
            var hash = {};

            array.forEach(function (val, idx) {
              hash[val] = true;
            });

            return hash;
          }


          function formatValue(ctx, value, recurseTimes) {
            // Provide a hook for user-specified inspect functions.
            // Check that value is an object with an inspect function on it
            if (ctx.customInspect &&
              value &&
              isFunction(value.inspect) &&
              // Filter out the util module, it's inspect function is special
              value.inspect !== exports.inspect &&
              // Also filter out any prototype objects using the circular check.
              !(value.constructor && value.constructor.prototype === value)) {
              var ret = value.inspect(recurseTimes, ctx);
              if (!isString(ret)) {
                ret = formatValue(ctx, ret, recurseTimes);
              }
              return ret;
            }

            // Primitive types cannot have properties
            var primitive = formatPrimitive(ctx, value);
            if (primitive) {
              return primitive;
            }

            // Look up the keys of the object.
            var keys = Object.keys(value);
            var visibleKeys = arrayToHash(keys);

            if (ctx.showHidden) {
              keys = Object.getOwnPropertyNames(value);
            }

            // IE doesn't make error fields non-enumerable
            // http://msdn.microsoft.com/en-us/library/ie/dww52sbt(v=vs.94).aspx
            if (isError(value)
              && (keys.indexOf('message') >= 0 || keys.indexOf('description') >= 0)) {
              return formatError(value);
            }

            // Some type of object without properties can be shortcutted.
            if (keys.length === 0) {
              if (isFunction(value)) {
                var name = value.name ? ': ' + value.name : '';
                return ctx.stylize('[Function' + name + ']', 'special');
              }
              if (isRegExp(value)) {
                return ctx.stylize(RegExp.prototype.toString.call(value), 'regexp');
              }
              if (isDate(value)) {
                return ctx.stylize(Date.prototype.toString.call(value), 'date');
              }
              if (isError(value)) {
                return formatError(value);
              }
            }

            var base = '', array = false, braces = ['{', '}'];

            // Make Array say that they are Array
            if (isArray(value)) {
              array = true;
              braces = ['[', ']'];
            }

            // Make functions say that they are functions
            if (isFunction(value)) {
              var n = value.name ? ': ' + value.name : '';
              base = ' [Function' + n + ']';
            }

            // Make RegExps say that they are RegExps
            if (isRegExp(value)) {
              base = ' ' + RegExp.prototype.toString.call(value);
            }

            // Make dates with properties first say the date
            if (isDate(value)) {
              base = ' ' + Date.prototype.toUTCString.call(value);
            }

            // Make error with message first say the error
            if (isError(value)) {
              base = ' ' + formatError(value);
            }

            if (keys.length === 0 && (!array || value.length == 0)) {
              return braces[0] + base + braces[1];
            }

            if (recurseTimes < 0) {
              if (isRegExp(value)) {
                return ctx.stylize(RegExp.prototype.toString.call(value), 'regexp');
              } else {
                return ctx.stylize('[Object]', 'special');
              }
            }

            ctx.seen.push(value);

            var output;
            if (array) {
              output = formatArray(ctx, value, recurseTimes, visibleKeys, keys);
            } else {
              output = keys.map(function (key) {
                return formatProperty(ctx, value, recurseTimes, visibleKeys, key, array);
              });
            }

            ctx.seen.pop();

            return reduceToSingleString(output, base, braces);
          }


          function formatPrimitive(ctx, value) {
            if (isUndefined(value))
              return ctx.stylize('undefined', 'undefined');
            if (isString(value)) {
              var simple = '\'' + JSON.stringify(value).replace(/^"|"$/g, '')
                .replace(/'/g, "\\'")
                .replace(/\\"/g, '"') + '\'';
              return ctx.stylize(simple, 'string');
            }
            if (isNumber(value))
              return ctx.stylize('' + value, 'number');
            if (isBoolean(value))
              return ctx.stylize('' + value, 'boolean');
            // For some reason typeof null is "object", so special case here.
            if (isNull(value))
              return ctx.stylize('null', 'null');
          }


          function formatError(value) {
            return '[' + Error.prototype.toString.call(value) + ']';
          }


          function formatArray(ctx, value, recurseTimes, visibleKeys, keys) {
            var output = [];
            for (var i = 0, l = value.length; i < l; ++i) {
              if (hasOwnProperty(value, String(i))) {
                output.push(formatProperty(ctx, value, recurseTimes, visibleKeys,
                  String(i), true));
              } else {
                output.push('');
              }
            }
            keys.forEach(function (key) {
              if (!key.match(/^\d+$/)) {
                output.push(formatProperty(ctx, value, recurseTimes, visibleKeys,
                  key, true));
              }
            });
            return output;
          }


          function formatProperty(ctx, value, recurseTimes, visibleKeys, key, array) {
            var name, str, desc;
            desc = Object.getOwnPropertyDescriptor(value, key) || { value: value[key] };
            if (desc.get) {
              if (desc.set) {
                str = ctx.stylize('[Getter/Setter]', 'special');
              } else {
                str = ctx.stylize('[Getter]', 'special');
              }
            } else {
              if (desc.set) {
                str = ctx.stylize('[Setter]', 'special');
              }
            }
            if (!hasOwnProperty(visibleKeys, key)) {
              name = '[' + key + ']';
            }
            if (!str) {
              if (ctx.seen.indexOf(desc.value) < 0) {
                if (isNull(recurseTimes)) {
                  str = formatValue(ctx, desc.value, null);
                } else {
                  str = formatValue(ctx, desc.value, recurseTimes - 1);
                }
                if (str.indexOf('\n') > -1) {
                  if (array) {
                    str = str.split('\n').map(function (line) {
                      return '  ' + line;
                    }).join('\n').slice(2);
                  } else {
                    str = '\n' + str.split('\n').map(function (line) {
                      return '   ' + line;
                    }).join('\n');
                  }
                }
              } else {
                str = ctx.stylize('[Circular]', 'special');
              }
            }
            if (isUndefined(name)) {
              if (array && key.match(/^\d+$/)) {
                return str;
              }
              name = JSON.stringify('' + key);
              if (name.match(/^"([a-zA-Z_][a-zA-Z_0-9]*)"$/)) {
                name = name.slice(1, -1);
                name = ctx.stylize(name, 'name');
              } else {
                name = name.replace(/'/g, "\\'")
                  .replace(/\\"/g, '"')
                  .replace(/(^"|"$)/g, "'");
                name = ctx.stylize(name, 'string');
              }
            }

            return name + ': ' + str;
          }


          function reduceToSingleString(output, base, braces) {
            var numLinesEst = 0;
            var length = output.reduce(function (prev, cur) {
              numLinesEst++;
              if (cur.indexOf('\n') >= 0) numLinesEst++;
              return prev + cur.replace(/\u001b\[\d\d?m/g, '').length + 1;
            }, 0);

            if (length > 60) {
              return braces[0] +
                (base === '' ? '' : base + '\n ') +
                ' ' +
                output.join(',\n  ') +
                ' ' +
                braces[1];
            }

            return braces[0] + base + ' ' + output.join(', ') + ' ' + braces[1];
          }


          // NOTE: These type checking functions intentionally don't use `instanceof`
          // because it is fragile and can be easily faked with `Object.create()`.
          exports.types = require('./support/types');

          function isArray(ar) {
            return Array.isArray(ar);
          }
          exports.isArray = isArray;

          function isBoolean(arg) {
            return typeof arg === 'boolean';
          }
          exports.isBoolean = isBoolean;

          function isNull(arg) {
            return arg === null;
          }
          exports.isNull = isNull;

          function isNullOrUndefined(arg) {
            return arg == null;
          }
          exports.isNullOrUndefined = isNullOrUndefined;

          function isNumber(arg) {
            return typeof arg === 'number';
          }
          exports.isNumber = isNumber;

          function isString(arg) {
            return typeof arg === 'string';
          }
          exports.isString = isString;

          function isSymbol(arg) {
            return typeof arg === 'symbol';
          }
          exports.isSymbol = isSymbol;

          function isUndefined(arg) {
            return arg === void 0;
          }
          exports.isUndefined = isUndefined;

          function isRegExp(re) {
            return isObject(re) && objectToString(re) === '[object RegExp]';
          }
          exports.isRegExp = isRegExp;
          exports.types.isRegExp = isRegExp;

          function isObject(arg) {
            return typeof arg === 'object' && arg !== null;
          }
          exports.isObject = isObject;

          function isDate(d) {
            return isObject(d) && objectToString(d) === '[object Date]';
          }
          exports.isDate = isDate;
          exports.types.isDate = isDate;

          function isError(e) {
            return isObject(e) &&
              (objectToString(e) === '[object Error]' || e instanceof Error);
          }
          exports.isError = isError;
          exports.types.isNativeError = isError;

          function isFunction(arg) {
            return typeof arg === 'function';
          }
          exports.isFunction = isFunction;

          function isPrimitive(arg) {
            return arg === null ||
              typeof arg === 'boolean' ||
              typeof arg === 'number' ||
              typeof arg === 'string' ||
              typeof arg === 'symbol' ||  // ES6 symbol
              typeof arg === 'undefined';
          }
          exports.isPrimitive = isPrimitive;

          exports.isBuffer = require('./support/isBuffer');

          function objectToString(o) {
            return Object.prototype.toString.call(o);
          }


          function pad(n) {
            return n < 10 ? '0' + n.toString(10) : n.toString(10);
          }


          var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep',
            'Oct', 'Nov', 'Dec'];

          // 26 Feb 16:19:34
          function timestamp() {
            var d = new Date();
            var time = [pad(d.getHours()),
            pad(d.getMinutes()),
            pad(d.getSeconds())].join(':');
            return [d.getDate(), months[d.getMonth()], time].join(' ');
          }


          // log is just a thin wrapper to console.log that prepends a timestamp
          exports.log = function () {
            console.log('%s - %s', timestamp(), exports.format.apply(exports, arguments));
          };


          /**
           * Inherit the prototype methods from one constructor into another.
           *
           * The Function.prototype.inherits from lang.js rewritten as a standalone
           * function (not on Function.prototype). NOTE: If this file is to be loaded
           * during bootstrapping this function needs to be rewritten using some native
           * functions as prototype setup using normal JavaScript does not work as
           * expected during bootstrapping (see mirror.js in r114903).
           *
           * @param {function} ctor Constructor function which needs to inherit the
           *     prototype.
           * @param {function} superCtor Constructor function to inherit prototype from.
           */
          exports.inherits = require('inherits');

          exports._extend = function (origin, add) {
            // Don't do anything if add isn't an object
            if (!add || !isObject(add)) return origin;

            var keys = Object.keys(add);
            var i = keys.length;
            while (i--) {
              origin[keys[i]] = add[keys[i]];
            }
            return origin;
          };

          function hasOwnProperty(obj, prop) {
            return Object.prototype.hasOwnProperty.call(obj, prop);
          }

          var kCustomPromisifiedSymbol = typeof Symbol !== 'undefined' ? Symbol('util.promisify.custom') : undefined;

          exports.promisify = function promisify(original) {
            if (typeof original !== 'function')
              throw new TypeError('The "original" argument must be of type Function');

            if (kCustomPromisifiedSymbol && original[kCustomPromisifiedSymbol]) {
              var fn = original[kCustomPromisifiedSymbol];
              if (typeof fn !== 'function') {
                throw new TypeError('The "util.promisify.custom" argument must be of type Function');
              }
              Object.defineProperty(fn, kCustomPromisifiedSymbol, {
                value: fn, enumerable: false, writable: false, configurable: true
              });
              return fn;
            }

            function fn() {
              var promiseResolve, promiseReject;
              var promise = new Promise(function (resolve, reject) {
                promiseResolve = resolve;
                promiseReject = reject;
              });

              var args = [];
              for (var i = 0; i < arguments.length; i++) {
                args.push(arguments[i]);
              }
              args.push(function (err, value) {
                if (err) {
                  promiseReject(err);
                } else {
                  promiseResolve(value);
                }
              });

              try {
                original.apply(this, args);
              } catch (err) {
                promiseReject(err);
              }

              return promise;
            }

            Object.setPrototypeOf(fn, Object.getPrototypeOf(original));

            if (kCustomPromisifiedSymbol) Object.defineProperty(fn, kCustomPromisifiedSymbol, {
              value: fn, enumerable: false, writable: false, configurable: true
            });
            return Object.defineProperties(
              fn,
              getOwnPropertyDescriptors(original)
            );
          }

          exports.promisify.custom = kCustomPromisifiedSymbol

          function callbackifyOnRejected(reason, cb) {
            // `!reason` guard inspired by bluebird (Ref: https://goo.gl/t5IS6M).
            // Because `null` is a special error value in callbacks which means "no error
            // occurred", we error-wrap so the callback consumer can distinguish between
            // "the promise rejected with null" or "the promise fulfilled with undefined".
            if (!reason) {
              var newReason = new Error('Promise was rejected with a falsy value');
              newReason.reason = reason;
              reason = newReason;
            }
            return cb(reason);
          }

          function callbackify(original) {
            if (typeof original !== 'function') {
              throw new TypeError('The "original" argument must be of type Function');
            }

            // We DO NOT return the promise as it gives the user a false sense that
            // the promise is actually somehow related to the callback's execution
            // and that the callback throwing will reject the promise.
            function callbackified() {
              var args = [];
              for (var i = 0; i < arguments.length; i++) {
                args.push(arguments[i]);
              }

              var maybeCb = args.pop();
              if (typeof maybeCb !== 'function') {
                throw new TypeError('The last argument must be of type Function');
              }
              var self = this;
              var cb = function () {
                return maybeCb.apply(self, arguments);
              };
              // In true node style we process the callback on `nextTick` with all the
              // implications (stack, `uncaughtException`, `async_hooks`)
              original.apply(this, args)
                .then(function (ret) { process.nextTick(cb.bind(null, null, ret)) },
                  function (rej) { process.nextTick(callbackifyOnRejected.bind(null, rej, cb)) });
            }

            Object.setPrototypeOf(callbackified, Object.getPrototypeOf(original));
            Object.defineProperties(callbackified,
              getOwnPropertyDescriptors(original));
            return callbackified;
          }
          exports.callbackify = callbackify;

        }).call(this)
      }).call(this, require('_process'))
    }, { "./support/isBuffer": 20, "./support/types": 21, "_process": 19, "inherits": 14 }], 23: [function (require, module, exports) {
      (function (global) {
        (function () {
          'use strict';

          var forEach = require('for-each');
          var availableTypedArrays = require('available-typed-arrays');
          var callBound = require('call-bind/callBound');
          var gOPD = require('gopd');

          var $toString = callBound('Object.prototype.toString');
          var hasToStringTag = require('has-tostringtag/shams')();

          var g = typeof globalThis === 'undefined' ? global : globalThis;
          var typedArrays = availableTypedArrays();

          var $slice = callBound('String.prototype.slice');
          var toStrTags = {};
          var getPrototypeOf = Object.getPrototypeOf; // require('getprototypeof');
          if (hasToStringTag && gOPD && getPrototypeOf) {
            forEach(typedArrays, function (typedArray) {
              if (typeof g[typedArray] === 'function') {
                var arr = new g[typedArray]();
                if (Symbol.toStringTag in arr) {
                  var proto = getPrototypeOf(arr);
                  var descriptor = gOPD(proto, Symbol.toStringTag);
                  if (!descriptor) {
                    var superProto = getPrototypeOf(proto);
                    descriptor = gOPD(superProto, Symbol.toStringTag);
                  }
                  toStrTags[typedArray] = descriptor.get;
                }
              }
            });
          }

          var tryTypedArrays = function tryAllTypedArrays(value) {
            var foundName = false;
            forEach(toStrTags, function (getter, typedArray) {
              if (!foundName) {
                try {
                  var name = getter.call(value);
                  if (name === typedArray) {
                    foundName = name;
                  }
                } catch (e) { }
              }
            });
            return foundName;
          };

          var isTypedArray = require('is-typed-array');

          module.exports = function whichTypedArray(value) {
            if (!isTypedArray(value)) { return false; }
            if (!hasToStringTag || !(Symbol.toStringTag in value)) { return $slice($toString(value), 8, -1); }
            return tryTypedArrays(value);
          };

        }).call(this)
      }).call(this, typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})
    }, { "available-typed-arrays": 2, "call-bind/callBound": 3, "for-each": 5, "gopd": 9, "has-tostringtag/shams": 12, "is-typed-array": 18 }], 24: [function (require, module, exports) {
      const { transporters } = require("./transporters.js");
      const { BaseChainableBridgeProxy } = require("./proxies.js");
      const { BaseChainableBridgeConnection } = require("./connection.js");
      const { proxymise, isRawObject } = require("./utils.js")
      const util = require("util");

      class BaseHandler {

        proxy = BaseChainableBridgeProxy
        connection = BaseChainableBridgeConnection;

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
            callable_proxy: (_prop, x, use_kwargs = false) => {
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
              if (item === value) {
                key = k;
                return;
              }
            } catch (err) { }
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
            ret = this.proxy(this, item);
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

          if ((key !== "value" && key !== "response" && key !== "args") || allow == false) {
            return value;
          }

          // console.log(key, value)

          try {
            if (value.toString() == "__JsBridgeProxyObject__") {
              return { type: "bridge_proxy", obj_type: "reverse_proxy", location: String(value.__data__.location), reverse: true };
            }
          } catch {}

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
                ret = { 'error': err.message }
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

        recieve(message = null) {
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
                if (data.error) {
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
          let ret;
          let func = this["handle_" + request.action];
          if (!func) throw Error("Invalid action.");

          if (request.action == "await_proxy") {
            ret = await func.call(this, request);
          }
          else { ret = func.call(this, request) }
          // console.log("Returning:", ret)
          return { response: ret };
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

        handle_call_proxy(req) {
          let ret,
            target = this.get_proxy(req.location);
          if (target) {
            let kwargs = [], args, i;
            let client = this;

            for (let i in req.kwargs) {
              kwargs.push(req.kwargs[i]);
            }

            args = [...req.args, ...kwargs]

            ret = target(...args);
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

            for (let i in req.kwargs) {
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
              } catch (err) { }
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

        get_result(response, property = null) {
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

      module.exports = {
        BaseHandler
      };
    }, { "./connection.js": 26, "./proxies.js": 28, "./transporters.js": 30, "./utils.js": 31, "util": 22 }], 25: [function (require, module, exports) {
      const { BaseHandler } = require("./base.js");
      const { transporters } = require("./transporters.js");
      const { BaseChainableBridgeProxy } = require("./proxies.js");
      const { PyBridgeConnection } = require("./connection.js");
      // const { proxymise } = require("./utils.js")
      const util = require("util")


      class JSBridgeClient extends BaseHandler {
        constructor(options) {
          super()
          this.options = options || {};
        }

        start() {
          let transporter = transporters[this.options.mode || "websocket"];
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

        set_mode(mode = "python") {
          if (mode === "python") {
            this.connection = PyBridgeConnection
            this.proxy = BaseChainableBridgeProxy
          }
        }

        create_connection(mode) {
          this.$ = this.connection(this.transporter, "", this)
        }

        format_arg(value) {
          let location;
          let value_type = typeof value;

          if (util.isNullOrUndefined(value)) {
            return null
          }

          if (value_type == "function" && String(value) == "__JsBridgeProxyObject__") {
            return { type: "bridge_proxy", obj_type: "reverse_proxy", location: String(value.__data__.location), reverse: true };
          }

          if (value_type == "string") {
            try {
              let is_number;
              try {
                is_number = new Number(value);
              } catch (err) { }

              if (!is_number) {
                let t = new Date(value);
                location = this.proxy_object(t);
                return { type: "bridge_proxy", obj_type: "date", location: location };
              }
            } catch (err) { }
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
          return { type: "bridge_proxy", obj_type: value_type, location: location };

          if (util.isSymbol(value)) {
            return { type: "bridge_proxy", obj_type: "symbol", location: location };
          }

          // if (util.types.isProxy(value)) {
          //   return { type: "bridge_proxy", obj_type: "proxy", location: location };
          // }

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

          if (value_type == 'object') { value_type = '' }

          return { type: "bridge_proxy", obj_type: value_type, location: location };
        }
      }

      // class PyBridgeClient extends JSBridgeClient {
      // connection = PyBridgeConnection
      // proxy = PyBridgeProxy
      // }

      module.exports = {
        JSBridgeClient,
        // PyBridgeClient
      };

    }, { "./base.js": 24, "./transporters.js": 30, "./proxies.js": 28, "./connection.js": 26, "util": 22 }], 26: [function (require, module, exports) {
      const { proxymise } = require("./utils.js")
      const util = require("util")


      const BaseBridgeConnectionHandler = {
        get: function (target, prop) {
          return proxymise(target.data.server.recieve({ action: "evaluate", value: prop }))
        }
      }

      class Intermediate extends Function {
        constructor(callstack, data) {
          super()
          this.callstack = [...callstack]
          this.data = data;
        }

        [util.inspect.custom]() {
          return '\n[You must use await when calling a Python API]\n'
        }
      }

      const BaseChainableBridgeConnectionHandler = {
        get: function (target, prop) {
          const next = new Intermediate(target.callstack, target.data)

          if (prop == "then") {
            return (resolve, reject) => {
              target.data.server.recieve({
                // session: PAGEID,
                action: "evaluate_stack_attribute",
                stack: target.callstack
              })
                .then(resolve).catch(reject);
            };
          }

          if (typeof prop === 'symbol') {
            if (prop === Symbol.iterator) {
              // This is just for destructuring arrays
              return function* iter() {
                for (let i = 0; i < 100; i++) {
                  const next = new Intermediate([...target.callstack, i])
                  yield new Proxy(next, handler)
                }
                throw SyntaxError('You must use `for await` when iterating over a Python object in a for-of loop')
              }
            }
            if (prop === Symbol.asyncIterator) {
              return async function* iter() {
                const it = await self.call(0, ['Iterate'], [{ ffid }])
                while (true) {
                  const val = await it.Next()
                  if (val === '$$STOPITER') {
                    return
                  } else {
                    yield val
                  }
                }
              }
            }
            // log('Get symbol', next.callstack, prop)
            return
          }
          if (Number.isInteger(parseInt(prop))) prop = parseInt(prop)
          next.callstack.push(prop)
          return new Proxy(next, BaseChainableBridgeConnectionHandler);
        },
        apply: function (target, _thisArg, args) {
          return new Promise((resolve, reject) => {
            let final = target.callstack[target.callstack.length - 1]
            let kwargs = {};
            let isolate = false;

            if (final === 'apply') {
              target.callstack.pop()
              args = [args[0], ...args[1]]
            } else if (final === 'call') {
              target.callstack.pop()
            } else if (final?.includes('$')) {
              kwargs = args.pop()

              if (final === "$") {
                target.callstack.pop();
              } else {
                if (final?.startsWith('$')) {
                  isolate = true;
                  final = final.slice(1)
                  target.callstack[target.callstack.length - 1] = final
                }
                if (final?.endsWith('$')) {
                  target.callstack[target.callstack.length - 1] = final.slice(0, -1)
                }
              }
            }

            target.data.server.recieve({
              // session: PAGEID,
              action: "call_stack_attribute",
              stack: target.callstack,
              // location: target.data.data.location,
              args: args,
              kwargs: kwargs,
              isolate
            })
              .then(resolve).catch(reject);

            target.callstack = [];
            return
          });
        }
      }

      const BaseBridgeConnection = (transporter, mode = "auto_eval", server = null, handler = BaseBridgeConnectionHandler) => {
        let __bridge__target__ = function () { }
        __bridge__target__.data = {
          transporter,
          mode, server
        };
        __bridge__target__.__bridge_proxy__ = true;
        let ret = new Proxy(__bridge__target__, handler);
        return ret;
      }

      const BaseChainableBridgeConnection = (transporter, mode = "auto_eval", server = null, handler = BaseChainableBridgeProxyHandler) => {
        return new Proxy(new Intermediate([], { transporter, mode, server }), handler)
      }

      const py_handlers = {
        "import": async function (target) {
          let rer = await this.data.server.recieve({ action: "import", value: target })
          // console.log("Returning:", rer)
          return rer
        },
        $: async function (tokens, ...replacements) {
          const vars = {} // List of locals
          let nstr = ''
          for (let i = 0; i < tokens.length; i++) {
            const token = tokens[i];
            const repl = await replacements[i]
            if (repl != null) {
              const v = '__' + i
              vars[v] = (repl.__bridge_proxy__ ? ({ location: repl.__bridge_data__.location }) : repl)
              nstr += token + v
            } else {
              nstr += token
            }
          }
          return await this.data.server.recieve({ action: "evaluate_code", code: nstr, locals: vars });
        }
      }

      const PyBridgeConnectionHandler = {
        get: function (target, prop) {
          if (py_handlers[prop]) {
            return py_handlers[prop].bind(target)
          }
          else {
            return BaseBridgeConnectionHandler.get(target, prop);
          }
        },
        apply: async function (target, thisArg, args) {
          let [tokens, ...replacements] = args;

          const vars = {} // List of locals
          let nstr = ''
          for (const token of tokens) {
            const repl = await replacements[i]
            if (repl != null) {
              const v = '__' + i
              vars[v] = (repl.__bridge_proxy__ ? ({ location: repl.__bridge_data__.location }) : repl)
              nstr += token + v
            } else {
              nstr += token
            }
          }
          return target.data.server.recieve({ action: "evaluate_code", code: nstr, locals: vars });
        }
      }

      const PyChainableBridgeConnectionHandler = {
        get: function (target, prop) {
          if (py_handlers[prop]) {
            return py_handlers[prop].bind(target)
          }
          else {
            return BaseChainableBridgeConnectionHandler.get(target, prop);
          }
        },
        apply: async function (target, thisArg, args) {
          let [tokens, ...replacements] = args;

          const vars = {} // List of locals
          let nstr = ''
          for (const token of tokens) {
            const repl = await replacements[i]
            if (repl != null) {
              const v = '__' + i
              vars[v] = (repl.__bridge_proxy__ ? ({ location: repl.__bridge_data__.location }) : repl)
              nstr += token + v
            } else {
              nstr += token
            }
          }
          return target.data.server.recieve({ action: "evaluate_code", code: nstr, locals: vars });
        }
      }

      const PyBridgeConnection = (transporter, mode = "auto_eval", server = null) => {
        if (mode == "auto_eva") {
          return BaseBridgeConnection(transporter, mode, server, PyBridgeConnectionHandler);
        } else {
          return BaseChainableBridgeConnection(transporter, mode, server, PyChainableBridgeConnectionHandler);
        }
      }

      module.exports = {
        BaseBridgeConnection,
        BaseBridgeConnectionHandler,
        BaseChainableBridgeConnection,
        BaseChainableBridgeConnectionHandler,
        PyBridgeConnection,
        PyBridgeConnectionHandler
      }

    }, { "./utils.js": 31, "util": 22 }], 27: [function (require, module, exports) {
      const transporters = require("./transporters.js");
      const clients = require("./client.js");
      const proxies = require("./proxies.js")
      const conns = require("./connection.js")
      const { proxymise } = require("./utils.js");

      class JSBridge {
        constructor() {

        }

        connect() {

        }
      }

      // let bridge = new JSBridge();
      // let py_server = new PyBridgeServer(mixin=StdIOBridgeTransporter);

      // let py = bridge.connect(py_server);

      // py.print("Hello From Python");

      // py.exit();

      module.exports = {
        JSBridge,
        ...clients,
        proxymise,
        ...proxies,
        ...conns,
        ...transporters
      }

    }, { "./client.js": 25, "./servers.js": 29, "./proxies.js": 28, "./connection.js": 26, "./transporters.js": 30, "./utils.js": 31 }], 28: [function (require, module, exports) {
      const { PyProxy, proxymise } = require("./utils.js")
      const util = require("util")

      const BaseBridgeProxyHandler = {
        get: function (target, property) {
          // console.log("Getting prop:", property, target)

          if (target[property] || property == "then") {
            return target[property]
          }

          if (property == "$") {
            return target.__conn__.formatters.callable_proxy(property, target.__data__, true)
          }

          let ret = new Promise((resolve, _reject) => {
            if (property === 'then') {
              return resolve(target.then);
            } else if (property === 'catch') {
              return resolve(target.catch);
            }

            if (property === "toJSON" || property == "constructor") {
              return target[property];
            }

            target.__conn__.recieve({
              // session: PAGEID,
              action: "get_proxy_attribute",
              target: typeof property == 'string' ? (property.endsWith("$") ? property.substring(0, property.length - 1) : property) : property,
              location: target.__data__.location,
            })
              .then((result) => {
                // console.log(property, "Result: ", result);
                try {
                  if (property.endsWith("$") && result.__data__) {
                    return resolve(target.__conn__.formatters.callable_proxy(null, result.__data__, true));
                  }
                  // result = target.__conn__.get_result(result, property);
                  // console.log("Resolving:", result)
                  resolve(result);
                } catch (error) {
                  return undefined;
                }

                // if (result == undefined) {
                //   if (property !== "then") {
                //     return reject("No attribute name: " + property);
                //   }
                // } else {
                // }
              });
          });
          if (ret) {
            ret = proxymise(ret);
          }
          return ret;
        },
        set: function (target, property, value) {
          if (property === "__proxy__") {
            target.__proxy__ = value;
            return true;
          }
          return proxymise(new Promise((resolve, _reject) => {
            target.__conn__.recieve({
              // session: PAGEID,
              action: "set_proxy_attribute",
              target: property,
              location: target.__data__.location,
              value: target.__conn__.format_arg(value),
            })
              .then((result) => resolve(result.value));
          }));
        },
        ownKeys: function (target) {
          return proxymise(new Promise((resolve, _reject) => {
            target.__conn__.recieve({
              // session: PAGEID,
              action: "get_proxy_attributes",
              location: target.__data__.location,
            })
              .then((result) => {
                resolve(Object.keys(result.value));
              });
          }));
        },
        deleteProperty: function (target, prop) {
          // to intercept property deletion
          return (new Promise((resolve, _reject) => {
            target.__conn__.recieve({
              // session: PAGEID,
              action: "delete_proxy_attribute",
              target: prop,
              location: target.__data__.location,
            })
              .then((result) => resolve(result.value));
          }));
        },
        has: function (target, prop) {
          return (new Promise((resolve, _reject) => {
            target.__conn__.recieve({
              // session: PAGEID,
              action: "has_proxy_attribute",
              target: prop,
              location: target.__data__.location
            })
              .then((result) => resolve(result.value));
          }));
        },
        apply: function (target, _thisArg, args) {
          return new Promise((resolve, _reject) => {
            target.__conn__.recieve({
              // session: PAGEID,
              action: "call_proxy",
              location: target.__data__.location,
              args: (args),
            })
              .then((result) => {
                // console.log("Calling proxy and returning:", target.__conn__.get_result(result));
                resolve(result)
              });
          });
        },
        construct: function (target, args) {
          return proxymise(new Promise((resolve, _reject) => {
            target.__conn__.recieve({
              // session: PAGEID,
              action: "call_proxy",
              location: target.__data__.location,
              args: (args),
            })
              .then((result) => resolve((result)));
          }));
        }
      }

      // Stolen from JSBridge.
      class Intermediate extends Function {
        constructor(callstack, data) {
          super()
          this.callstack = [...callstack]
          this.data = data;
          this.keys = Reflect.ownKeys(this);
        }

        [util.inspect.custom]() {
          return '\n[You must use await when calling a Python API]\n'
        }
      }
      // End

      const BaseChainableBridgeProxyHandler = {
        get: function (target, property) {
          // console.log("Getting prop:", property);

          if (property === "__bridge_data__") {
            return target.data.data;
          }

          if (property === "__bridge_proxy__") {
            return true;
          }

          if (property == "toJSON") {
            return () => ({ type: "bridge_proxy", obj_type: "reverse_proxy", location: target.data.data.location, reverse: true, stack: target.callstack })
          }

          if (property == "then") {
            if (target.callstack.length) {
              return (resolve, reject) => {
                target.data.server.recieve({
                  // session: PAGEID,
                  action: "get_stack_attribute",
                  stack: target.callstack,
                  location: target.data.data.location,
                })
                  .then(resolve).catch(reject);
              };
            } else {
              return undefined
            }
          }

          if (typeof property === 'symbol') {
            if (property === Symbol.iterator) {
              // This is just for destructuring arrays
              return function* iter() {
                for (let i = 0; i < 100; i++) {
                  const next = new Intermediate([...target.callstack, i])
                  yield new Proxy(next, BaseChainableBridgeProxyHandler)
                }
                throw SyntaxError('You must use `for await` when iterating over a Python object in a for-of loop')
              }
            }
            if (property === Symbol.asyncIterator) {
              return async function* iter() {
                const it = await self.call(0, ['Iterate'], [{ ffid }])
                while (true) {
                  const val = await it.Next()
                  if (val === '$$STOPITER') {
                    return
                  } else {
                    yield val
                  }
                }
              }
            }
            // log('Get symbol', next.callstack, property)
            return
          }
          if (Number.isInteger(parseInt(property))) property = parseInt(property)
          const next = new Intermediate(target.callstack, target.data);
          next.callstack.push(property)
          return new Proxy(next, BaseChainableBridgeProxyHandler);
        },

        set: function (target, property, value) {
          return new Promise((resolve, reject) => {
            target.data.server.recieve({
              // session: PAGEID,
              action: "set_stack_attribute",
              stack: target.callstack,
              location: target.data.data.location,
              value: value
            })
              .then(resolve).catch(reject);
          });
        },
        ownKeys: function (target) {
          target.data.server.recieve({
            // session: PAGEID,
            action: "get_stack_attributes",
            stack: target.callstack,
            location: target.data.data.location,
          })
            .then(data => {
              target.keys = data;
            })
          return [...new Set([...Reflect.ownKeys(target), ...target.keys])];
        },
        deleteProperty: function (target, prop) {
          // to intercept property deletion
          return (new Promise((resolve, _reject) => {
            target.data.server.recieve({
              // session: PAGEID,
              action: "delete_proxy_attribute",
              target: prop,
              location: target.__data__.location,
            })
              .then((result) => resolve(result.value));
          }));
        },
        has: function (target, prop) {
          return (new Promise((resolve, _reject) => {
            target.data.server.recieve({
              // session: PAGEID,
              action: "has_proxy_attribute",
              target: prop,
              location: target.__data__.location
            })
              .then((result) => resolve(result.value));
          }));
        },
        apply: function (target, thisArg, args) {
          return new Promise((resolve, reject) => {
            let final = target.callstack[target.callstack.length - 1]
            let kwargs = {};
            let isolate = false;

            if (final === 'apply') {
              target.callstack.pop()
              args = [args[0], ...args[1]]
            } else if (final === 'call') {
              target.callstack.pop()
            } else if (final?.includes('$')) {
              kwargs = args.pop()

              if (final === "$") {
                target.callstack.pop();
              } else {
                if (final?.startsWith('$')) {
                  isolate = true;
                  final = final.slice(1)
                  target.callstack[target.callstack.length - 1] = final
                }
                if (final?.endsWith('$')) {
                  target.callstack[target.callstack.length - 1] = final.slice(0, -1)
                }
              }
            }
            // } else if (final === 'valueOf') {
            //   target.callstack.pop()
            //   const ret = this.value(ffid, [...target.callstack])
            //   return ret
            // } else if (final === 'toString') {
            //   target.callstack.pop()
            //   const ret = this.inspect(ffid, [...target.callstack])
            //   return ret
            // }
            kwargs['this'] = thisArg;

            target.data.server.recieve({
              // session: PAGEID,
              action: "call_stack_attribute",
              stack: target.callstack,
              location: target.data.data.location,
              args, kwargs, isolate
            })
              .then(resolve).catch(reject);

            target.callstack = [];
            return
          });
        },
        construct: function (target, args) {
          return proxymise(new Promise((resolve, _reject) => {
            target.data.server.recieve({
              // session: PAGEID,
              action: "call_proxy",
              location: target.__data__.location,
              args: (args),
            })
              .then((result) => resolve((result)));
          }));
        }
      }

      const BaseBridgeProxy = (conn, data, handler = BaseBridgeProxyHandler) => {
        let __target__ = function () { }
        __target__.toString = () => "__JsBridgeProxyObject__"
        __target__.__conn__ = conn;
        __target__.__data__ = data;
        __target__.__bridge_proxy__ = true;
        __target__[Symbol.toPrimitive] = "__JsBridgeProxyObject__"
        return new Proxy(__target__, handler);
      }

      const BaseChainableBridgeProxy = (conn, data, handler = BaseChainableBridgeProxyHandler) => {
        return new Proxy(new Intermediate([], {
          server: conn,
          data: data
        }), handler);
      }

      // class BaseBridgeProxy {
      //     constructor(connection, data) {
      //         this.__conn__ = connection
      //         this.__data__ = data
      //     }

      //     // __cast__(target=String):
      //     //     return target(this.__conn__.recieve(
      //     //         action="get_primitive",
      //     //         location=this.__data__['location']
      //     //     ))

      //     __call__(...args) {
      //         return this.__conn__.recieve(
      //             action="call_proxy",
      //             location=this.__data__['location'],
      //             args=this.__conn__.format_args(args),
      //             kwargs={}
      //         )
      //     }

      //     __getattr__(name) {
      //         return this.__conn__.recieve(
      //             action="get_proxy_attribute",
      //             location=this.__data__['location'],
      //             target=name
      //         )
      //     }

      //     __setattr__(name, value) {
      //         return this.__conn__.recieve(
      //             action="set_proxy_attribute",
      //             location=this.__data__['location'],
      //             target=name,
      //             value=this.__conn__.format_args(value)
      //         )
      //     }

      //     // __getitem__(index):
      //     //     return this.__conn__.recieve(
      //     //         action="get_proxy_index",
      //     //         location=this.__data__['location'],
      //     //         target=index
      //     //     )


      //     // __str__(this):
      //     //     return this.__cast__()
      // }


      // class PyBridgeProxy extends BaseBridgeProxy {

      // }


      // class RubyBridgeProxy extends BaseBridgeProxy {

      // }


      // class JavaBridgeProxy extends BaseBridgeProxy {

      // }


      // class CSharpBridgeProxy extends BaseBridgeProxy {

      // }


      // class GoLangBridgeProxy extends BaseBridgeProxy {

      // }

      function generateProxy(_class) {
        return PyProxy(_class)
      }


      module.exports = {
        BaseBridgeProxy,
        BaseChainableBridgeProxy
        // generateProxy,
        // PyBridgeProxy,
        // GoLangBridgeProxy,
        // JavaBridgeProxy,
        // RubyBridgeProxy
      }
    }, { "./utils.js": 31, "util": 22 }], 29: [
      function (require, module, exports) {
        const { BaseHandler } = require("./base.js");
        const { BaseBridgeConnection, PyBridgeConnection } = require("./connection.js");
        const { BaseBridgeProxy, BaseChainableBridgeProxy } = require("./proxies.js");
        const { isRawObject } = require("./utils.js")

        const util = require("util")

        class BaseBridgeServer extends BaseHandler {
          args = [];
          import_alias = 'bridge';

          proxy = BaseBridgeProxy;
          connection = BaseBridgeConnection;

          constructor(transporter = null, keep_alive = false, timeout = 5) {
            super();
            this.transporter = transporter || this.default_transporter()
            this.timeout = timeout

            this.__keep_alive = keep_alive
          }

          setup_imports(name) {
          }


          import_lib(name) {
            return
          }

          setup(name = null, ...a) {
            let conn = this.start(...a)
            this.setup_imports(name || this.import_alias)
            return conn
          }

          start(bridge = null, mode = "chain") {
            this.bridge = bridge
            this.conn = this.create_connection(mode = mode)
            this.transporter.start(
              this.on_message.bind(this),
              this
            )
            return this.conn
          }

          create_connection(mode) {
            return this.connection(
              this.transporter,
              mode, this
            )
          }

          __keep_alive__() {
            this.__keep_alive = true
          }

          stop(force = false) {
            if (!(force && this.__keep_alive)) {
              return
            }
            this.transporter.stop()
          }

          async on_message(message) {
            if (message.action) {
              let response = await this.process_command(message)
              response.message_id = message.message_id
              return this.transporter.send(response)
            }
            else {
              let handler = this.message_handlers.get(message.message_id)
              if (handler) return handler(message)
              else {
                if (message.response) {
                  message = message.response
                }
                else if (message.value) {
                  message = message.value
                }
                return
              }
            }
            return
          }

          encoder(key, value) {

            if (util.types.isProxy(value) || value?.__bridge_proxy__) {
              return { type: "bridge_proxy", obj_type: "reverse_proxy", location: String(value.__data__.location), reverse: true };
            }

            if (isRawObject(value)) {
              return value;
            }

            return this.format_arg(value);
          }


          format_arg(value) {
            let location;
            let value_type = typeof value;

            if (value === null || value === undefined) {
              return null
            }

            if (util.types.isProxy(value) || value?.__bridge_proxy__) {
              return { type: "bridge_proxy", obj_type: "reverse_proxy", location: String(value.__data__.location), reverse: true };
            }

            if (value_type == "string") {
              try {
                let is_number;
                try {
                  is_number = new Number(value);
                } catch (err) { }

                if (!is_number) {
                  let t = new Date(value);
                  location = this.proxy_object(t);
                  return { type: "bridge_proxy", obj_type: "date", location: location };
                }
              } catch (err) { }
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


            if (util.isBuffer(value)) {
              return { type: "bridge_proxy", obj_type: "bytes", location: location }
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

            if (util.types.isDate(value)) {
              return { type: "bridge_proxy", obj_type: "date", location: location };
            }

            return { type: "bridge_proxy", obj_type: value_type, location: location };
          }

        }


        class PyBridgeServer extends BaseBridgeServer {
          args = ["python", "-m", "py_bridge"]

          proxy = BaseChainableBridgeProxy
          connection = PyBridgeConnection
        }


        class RubyBridgeServer extends BaseBridgeServer {

        }


        class JavaBridgeServer extends BaseBridgeServer {

        }


        class CSharpBridgeServer extends BaseBridgeServer {

        }


        class GoLangBridgeServer extends BaseBridgeServer {

        }


        module.exports = {
          BaseBridgeServer,
          PyBridgeServer,
          RubyBridgeServer,
          JavaBridgeServer,
          CSharpBridgeServer,
          GoLangBridgeServer
        }
      }, { "./base.js": 24, "./connection.js": 26, "./proxies.js": 28, "./utils.js": 31, "util": 22 }], 30: [function (require, module, exports) {
        (function (process) {
          (function () {
            const fs = require("fs");

            class BaseBridgeTransporter {

              start(on_message, server) {
                this.on_message = on_message
                this.bridge = server
                this.setup()
              }

              setup() { }

              decode(data, raw = false) {
                return (!raw) ? JSON.parse(data, this.bridge.decoder.bind(this.bridge)) : JSON.parse(data)
              }

              encode(data, raw = false) {
                // console.log("[JS] Encoding:", data)
                return (!raw) ? JSON.stringify(data, this.bridge.encoder.bind(this.bridge)) : JSON.stringify(data)
              }

            }

            class StdIOBridgeTransporter extends BaseBridgeTransporter {
              start_client(on_message, options, bridge) {
                this.listening = true;
                this.on_message = on_message;
                this.bridge = bridge;

                this.stdin = options.stdin;
                this.stdout = options.stdout;
                this.start_listening()
              }

              send(data, raw = false) {
                data = this.encode(data, raw)
                // console.log("[JS] Sent:", data);
                fs.writeFileSync(this.stdout, data, "utf-8");
              }

              start_listening(mode = "listening") {
                let target;
                if (mode == "listening") target = this.stdin
                else target = this.stdout

                // console.log("[JS] Started listening");

                // while (this.listening) {
                //  let data = fs.readFileSync(this.stdin).toString();
                //  if (data) {
                //    console.log("[JS} Recieved:", data);
                //    this.on_message(this.decode(data, true))
                //    fs.writeFileSync(this.stdin, "", "utf-8");
                //  }
                // }

                setInterval(() => {
                  let data = fs.readFileSync(this.stdin, "utf-8");
                  //      console.log("Data:",data)
                  if (data) {
                    // console.log("[JS} Recieved:", data);
                    this.on_message(this.decode(data))
                    fs.writeFileSync(this.stdin, "", "utf-8");
                  }
                }, 100)
              }
            }

            class WebSocketBridgeTransporter extends BaseBridgeTransporter {
              start_client(on_message, options, bridge) {
                this.listening = true;
                this.on_message = on_message;
                this.bridge = bridge;
                this.options = options;

                this.host = options.host || "localhost";
                this.port = options.port || 7001;
                this.path = options.path || "/"

                this.socket = new WebSocket(`ws://${this.host}:${this.port}${this.path}`)

                this.start_listening()
              }

              send(data, raw = false) {
                 // console.log("[JS} To Send:", data);
                data['conn_id'] = this.options.conn_id
                data = this.encode(data, raw)
                this.options.debug && console.log("[JS} Sent:", data);
                this.socket.send(data + "\n")
              }

              start_listening() {
                this.socket.onmessage = (ev) => {
                  let data = ev.data
                  let _this = this;

                  function main(data) {
                    // console.log("[JS} Recieved:", data);
                    for (let item of data.split("\n")) {
                      item = item.trim();
                      if (item) {
                        _this.options.debug && console.log("[JS} Recieved:", item);
                        _this.on_message(_this.decode(item));
                      }
                    }
                  }

                  if (data instanceof Blob) {
                    data.text().then(main)
                  } else {
                    main(data)
                  }

                }
              }
            }


            // class SocketIOBridgeTransporter extends BaseBridgeTransporter {
            //     constructor(host='127.0.0.1', port=7001) {
            //         this.host = host
            //         this.port = port
            //         this.socket = null
            //         this.listening = true
            //         this.tasks = []
            //     }

            //     get_setup_args(args, kw) {
            //         return [args, kw]
            //     }

            //     send(data, raw=false) {
            //         data = this.encode(data, raw)
            //         if (this.socket) {
            //             try {
            //                 this.socket.emit("message", data + "\n")
            //             }
            //             catch (err) {
            //                 this.listening = false
            //             }
            //         } else {
            //             this.tasks.append(data)
            //         }
            //     }

            //     setup_app() {
            //        const http = require('http');
            //    const server = http.createServer();
            //    const { Server } = require("socket.io");
            //    const io = new Server(server);

            //    let _this = this; 

            //    io.on('connection', (socket) => {
            //      _this.socket = socket;
            //      socket.on('message', (data) => {
            //        // data = data.toString()
            //            for (let item of data.split("\n")) {
            //              item = item.trim();
            //              if (item) {
            //                // console.log("[JS} Recieved:", item);
            //                this.on_message(this.decode(item));
            //              }
            //            }
            //      });
            //    });

            //    server.listen(3000, () => {
            //      console.log('listening on *:3000');
            //    });
            //     }

            //     setup() {
            //         this.setup_app()
            //     }

            //     start_client(on_message, options=null, server=null) {
            //         options = options || {}
            //         this.on_message = on_message
            //         this.server = server
            //         this.host = options.get("host", "localhost")
            //         this.port = options.get("port", 7000)

            //         this.setup_app()
            //     }
            // }


            let transporters = {
              "stdio": StdIOBridgeTransporter,
              "websocket": WebSocketBridgeTransporter,
              // "socketio": SocketIOBridgeTransporter
            }

            module.exports = {
              transporters,
              BaseBridgeTransporter,
              StdIOBridgeTransporter,
              WebSocketBridgeTransporter
            }
          }).call(this)
        }).call(this, require('_process'))
      }, { "_process": 19, "child_process": 1, "fs": 1, "net": 1, "ws": 32 }], 31: [function (require, module, exports) {
        const util = require("util")

        PyProxy = (_class) => {
          let proxy = new Proxy(
            (_class),
            {
              get: function (target, property) {
                // console.log("get called");
                if (target[property]) {
                  return target[property]
                }
                return target.__getattr__?.bind(target)(property);
              },
              set: function (target, property, value) {
                if (target[property]) {
                  target[property] = value;
                  return true
                }
                return target.__setattr__?.bind(target)(property, value);
              },
              ownKeys: function (target) {
                return target.__ownkeys__?.bind(target)(prop);
              },
              deleteProperty: function (target, prop) {
                return target.__delattr__?.bind(target)(prop);
              },
              has: function (target, prop) {
                return target.__hasattr__?.bind(target)(prop);
              },
              apply: function (target, _thisArg, args) {
                return target.__call__?.bind(target)(...args);
              },
              construct: function (target, args) {
                return target.__construct__?.bind(target)(...args);
              },
              // getPrototypeOf: function(target) {
              //   return target.prototype;
              // },
              // defineProperty: function(target, property, attribute) {
              //   console.log("define called");
              //   return true;
              // }
            }
          );
          return proxy;
        };

        let handlers = {
          construct(target, argumentsList) {
            if (target.__is_proxy__) target = target();
            return proxymise(Reflect.construct(target, argumentsList));
          },

          get(target, property, receiver) {
            if (target.__is_proxy__) target = target();
            // console.log("Getting:", target, property)
            if (property !== 'then' && property !== 'catch' && typeof target.then === 'function') {
              return proxymise(target.then(value => get(value, property, receiver)));
            }
            return proxymise(get(target, property, receiver));
          },

          apply(target, thisArg, argumentsList) {
            if (target.__is_proxy__) target = target();
            // console.log("Calling:", target, thisArg)
            if (typeof target.then === 'function') {
              return proxymise(target.then(value => {
                console.log(value);
                return Reflect.apply(value, thisArg, argumentsList)
              }));
            }
            return proxymise(Reflect.apply(target, thisArg, argumentsList));
          }
        }

        function proxymise(target) {
          // console.log('Proxymising:', target)
          if (!util.types.isPromise(target)) return target;

          let ret;
          if ((typeof target === 'object' && !target?.__bridge_proxy__)) {
            const proxy = () => target;
            proxy.__is_proxy__ = true;
            ret = new Proxy(proxy, handlers);
          } else {
            if (typeof target === 'function') {
              ret = new Proxy(target, handlers);
            } else {
              return target
            }
            ret.__proxymised__ = true;
          }
          return ret;
        };

        function get(target, property, receiver) {
          // console.log("Gettingng:", target, property)
          const value = (typeof target === 'object') ? Reflect.get(target, property, receiver) : target[property];
          if (typeof value === 'function' && typeof value.bind === 'function') {
            return Object.assign(value.bind(target), value);
          }
          return value;
        };

        function isRawObject(item) {
          return (item instanceof Object && item.constructor == Object().constructor)
        }

        module.exports = {
          PyProxy,
          proxymise,
          isRawObject
        }

      }, { "util": 22 }], 32: [function (require, module, exports) {
        'use strict';

        module.exports = function () {
          throw new Error(
            'ws does not work in the browser. Browser clients must use the native ' +
            'WebSocket object'
          );
        };

      }, {}]
  }, {}, [27])(27)
});
