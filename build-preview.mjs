import { cp, rm } from "node:fs/promises";
import { resolve } from "node:path";

const root = resolve(import.meta.dirname);
const source = resolve(root, "web-preview");
const output = resolve(root, "dist");

await rm(output, { recursive: true, force: true });
await cp(source, output, { recursive: true });
