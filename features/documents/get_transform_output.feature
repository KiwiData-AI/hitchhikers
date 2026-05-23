Feature: Get document transform output
  As a developer integrating with the Kiwi DAIS API
  I want to retrieve the transformed output state for a specific document
  So that I can access the client-facing result of the document processing pipeline

  Background:
    Given a KiwiClient configured with a valid API key

  Scenario: Get transform output for a completed document
    Given a document exists that has completed transformation
    When I call get_transform_output with that document_id
    Then the response contains the transformed output for the document

  Scenario: Get transform output for an unfinished document
    Given a document exists that has not yet completed transformation
    When I call get_transform_output with that document_id
    Then the response reflects the current incomplete transform state

  Scenario: Get transform output returns not found for unknown ID
    When I call get_transform_output with a non-existent document_id
    Then a NotFoundError is raised

  Scenario: Invalid API key is rejected
    Given a KiwiClient configured with an invalid API key
    When I call get_transform_output with any document_id
    Then an AuthenticationError is raised
