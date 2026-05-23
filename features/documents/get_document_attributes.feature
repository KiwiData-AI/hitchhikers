Feature: Get document attributes
  As a developer integrating with the Kiwi DAIS API
  I want to retrieve the extracted attribute payloads for a document
  So that I can access structured data extracted from the document content

  Background:
    Given a KiwiClient configured with a valid API key

  Scenario: Get attributes for a processed document
    Given a document exists with extracted attributes
    When I call get_document_attributes with that document_id
    Then the response is a list of extraction payload widgets
    And each widget has a schema_name, schema_version, and payload

  Scenario: Get attributes returns empty list for unprocessed document
    Given a document exists with no extracted attributes yet
    When I call get_document_attributes with that document_id
    Then the response is an empty list

  Scenario: Get attributes returns not found for unknown ID
    When I call get_document_attributes with a non-existent document_id
    Then a NotFoundError is raised

  Scenario: Invalid API key is rejected
    Given a KiwiClient configured with an invalid API key
    When I call get_document_attributes with any document_id
    Then an AuthenticationError is raised
