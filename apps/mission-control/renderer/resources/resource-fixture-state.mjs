import {
  currentResourceFixture,
  historicalResourceFixture,
} from "./resource-fixture.mjs";
import { RESOURCE_MESSAGES } from "./resource-messages.mjs";

export const RESOURCE_FIXTURE_MESSAGES = Object.freeze({
  "en-US": Object.freeze({
    ...RESOURCE_MESSAGES["en-US"],
    "resource.fixture": "REFERENCE RESOURCE DATA",
  }),
});

export function referenceResourceState() {
  return Object.freeze({
    current: currentResourceFixture(),
    comparison: historicalResourceFixture(),
    comparisonState: "PRESENT",
  });
}

export const RESOURCE_FIXTURE_SUPPORT = Object.freeze({
  referenceState: referenceResourceState,
  historicalProfile: historicalResourceFixture,
  messages: RESOURCE_FIXTURE_MESSAGES,
});
