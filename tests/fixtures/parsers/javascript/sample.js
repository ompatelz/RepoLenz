/**
 * @fileoverview Sample JavaScript file mixing CommonJS and ES6 constructs for static analysis testing.
 */

const path = require('path');
const fs = require('fs');

/**
 * In-memory event dispatcher class.
 */
class EventEmitter {
  constructor() {
    this.events = {};
  }

  /**
   * Register a callback listener for a topic.
   * @param {string} event
   * @param {Function} listener
   */
  on(event, listener) {
    if (!this.events[event]) {
      this.events[event] = [];
    }
    this.events[event].push(listener);
  }

  /**
   * Broadcast arguments to registered listeners.
   * @param {string} event
   * @param {...any} args
   */
  emit(event, ...args) {
    const listeners = this.events[event] || [];
    for (const listener of listeners) {
      listener(...args);
    }
  }
}

/**
 * Resolves a normalized relative path.
 * @param {string} filepath
 * @returns {string} Normalized POSIX path
 */
function helper(filepath) {
  return path.normalize(filepath).replace(/\\/g, '/');
}

/**
 * Arrow function converting input text to uppercase.
 * @param {string} text
 * @returns {string}
 */
const toUpper = (text) => {
  return String(text).toUpperCase();
};

module.exports = {
  EventEmitter,
  helper,
  toUpper,
};
