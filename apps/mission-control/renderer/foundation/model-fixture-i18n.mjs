import {
  createTranslator,
  DEFAULT_LOCALE,
  FOUNDATION_MESSAGES,
} from "./i18n.mjs";
import { MODEL_FIXTURE_MESSAGES } from "./messages/model-fixture.mjs";

const MODEL_FIXTURE_CATALOG = Object.freeze({
  ...FOUNDATION_MESSAGES[DEFAULT_LOCALE],
  ...MODEL_FIXTURE_MESSAGES,
});

export const modelFixtureT = createTranslator({
  messages: Object.freeze({ [DEFAULT_LOCALE]: MODEL_FIXTURE_CATALOG }),
});
