"use strict";

const {
  assertRendererRequest,
  assertRendererSafePayload,
  assertStableRef,
} = require("./validation.cjs");

class ControlPlaneBridge {
  constructor(adapter, validators, { onSecurityViolation } = {}) {
    if (!adapter || typeof adapter.connect !== "function") {
      throw new TypeError("BAMF_GUI20_CONTROL_PLANE_ADAPTER_REQUIRED");
    }
    for (const name of [
      "publicStatus",
      "snapshotRequest",
      "queryRequest",
      "dryRunRequest",
      "commandRequest",
      "receiptRef",
      "response",
      "event",
    ]) {
      if (!validators || typeof validators[name] !== "function") {
        throw new TypeError(`BAMF_GUI20_CP02_VALIDATOR_REQUIRED:${name}`);
      }
    }
    this.adapter = adapter;
    this.validators = validators;
    this.onSecurityViolation = typeof onSecurityViolation === "function" ? onSecurityViolation : null;
    this.session = null;
    this.connectionEpoch = 0;
    this.subscriptions = new Set();
  }

  async connect() {
    await this.#invalidateSession();
    const connection = await this.adapter.connect();
    if (!connection || typeof connection !== "object" || !("session" in connection)) {
      throw new TypeError("BAMF_GUI20_CONTROL_PLANE_HANDSHAKE_INVALID");
    }
    let publicStatus;
    try {
      publicStatus = this.validators.publicStatus(
        assertRendererSafePayload(connection.publicStatus ?? {}),
      );
    } catch (error) {
      if (typeof this.adapter.disconnect === "function") {
        await this.adapter.disconnect(connection.session);
      }
      throw error;
    }
    this.session = connection.session;
    this.connectionEpoch += 1;
    return Object.freeze({ ...publicStatus, connectionEpoch: this.connectionEpoch });
  }

  async disconnect() {
    await this.#invalidateSession();
    this.connectionEpoch += 1;
    return Object.freeze({ state: "DISCONNECTED", connectionEpoch: this.connectionEpoch });
  }

  async status() {
    return this.#call("status");
  }

  async snapshot(request) {
    const safe = assertRendererRequest(request);
    return this.#call("snapshot", this.validators.snapshotRequest(safe));
  }

  async query(request) {
    const safe = assertRendererRequest(request);
    return this.#call("query", this.validators.queryRequest(safe));
  }

  async dryRun(request) {
    const safe = assertRendererRequest(request);
    return this.#call("dryRun", this.validators.dryRunRequest(safe));
  }

  async command(request) {
    const safe = assertRendererRequest(request);
    return this.#call("command", this.validators.commandRequest(safe));
  }

  async receipt(ref) {
    const safe = assertStableRef(ref);
    return this.#call("receipt", this.validators.receiptRef(safe));
  }

  async subscribe(listener) {
    if (typeof listener !== "function") {
      throw new TypeError("BAMF_GUI20_EVENT_LISTENER_REQUIRED");
    }
    const session = this.#requireSession();
    if (typeof this.adapter.subscribe !== "function") {
      throw new TypeError("BAMF_GUI20_CONTROL_PLANE_METHOD_UNAVAILABLE:subscribe");
    }
    const epoch = this.connectionEpoch;
    const unsubscribe = await this.adapter.subscribe(session, (payload) => {
      if (this.session !== session || this.connectionEpoch !== epoch) {
        return;
      }
      try {
        const safe = assertRendererSafePayload(payload);
        listener(this.validators.event(safe));
      } catch (error) {
        this.onSecurityViolation?.(
          typeof error?.code === "string" ? error.code : "BAMF_GUI20_EVENT_REJECTED",
        );
      }
    });
    if (typeof unsubscribe !== "function") {
      throw new TypeError("BAMF_GUI20_CONTROL_PLANE_SUBSCRIPTION_INVALID");
    }
    this.subscriptions.add(unsubscribe);
    return () => {
      if (!this.subscriptions.delete(unsubscribe)) {
        return;
      }
      unsubscribe();
    };
  }

  #requireSession() {
    if (this.session === null) {
      const error = new Error("BAMF_GUI20_CONTROL_PLANE_NOT_CONNECTED");
      error.code = "BAMF_GUI20_CONTROL_PLANE_NOT_CONNECTED";
      throw error;
    }
    return this.session;
  }

  async #call(method, argument) {
    const session = this.#requireSession();
    if (typeof this.adapter[method] !== "function") {
      throw new TypeError(`BAMF_GUI20_CONTROL_PLANE_METHOD_UNAVAILABLE:${method}`);
    }
    const result = argument === undefined
      ? await this.adapter[method](session)
      : await this.adapter[method](session, argument);
    return this.validators.response(method, assertRendererSafePayload(result), argument);
  }

  async #invalidateSession() {
    for (const unsubscribe of this.subscriptions) {
      unsubscribe();
    }
    this.subscriptions.clear();
    if (this.session !== null && typeof this.adapter.disconnect === "function") {
      await this.adapter.disconnect(this.session);
    }
    this.session = null;
  }
}

module.exports = { ControlPlaneBridge };
