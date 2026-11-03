import test from "node:test";
import assert from "node:assert/strict";
import { healthStatus } from "../src/index.js";

test("healthStatus reports the service as healthy", () => {
  assert.deepEqual(healthStatus(), { status: "ok" });
});
