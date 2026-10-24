import { readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

/** The API's golden outputs: real responses, shared with the backend test suite. */
export const API_FIXTURES_DIR = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "../../../tests/fixtures/pnr",
);

export function readApiFixture(gds: string, name: string): unknown {
  return JSON.parse(readFileSync(join(API_FIXTURES_DIR, gds, `${name}.expected.json`), "utf8"));
}

export function listApiFixtures(): { id: string; gds: string; name: string }[] {
  return readdirSync(API_FIXTURES_DIR).flatMap((gds) =>
    readdirSync(join(API_FIXTURES_DIR, gds))
      .filter((file) => file.endsWith(".expected.json"))
      .map((file) => {
        const name = file.replace(".expected.json", "");
        return { id: `${gds}/${name}`, gds, name };
      }),
  );
}
