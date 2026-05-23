Feature: Get document details
  As a developer integrating with the Kiwi DAIS API
  I want to retrieve key details and processing state of a specific document
  So that I can check its status and metadata

  Background:
    Given a KiwiClient configured with a valid API key

  Scenario: Get document by valid ID
    Given a document exists with a known document_id
    When I call get_document with that document_id
    Then the response contains the document_id, title, state, and doc_type

  Scenario: Get document returns not found for unknown ID
    When I call get_document with a non-existent document_id
    Then a NotFoundError is raised

  Scenario: Invalid API key is rejected
    Given a KiwiClient configured with an invalid API key
    When I call get_document with any document_id
    Then an AuthenticationError is raised
