import { expect, test } from "bun:test";
import { greeting } from "./index.js";

test("greets the supplied name", () => {
  expect(greeting("ArpScayl")).toBe("Hello, ArpScayl");
});
