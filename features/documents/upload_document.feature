Feature: Upload document
  As a developer integrating with the Kiwi DAIS API
  I want to upload a document for processing
  So that attributes can be extracted and the document tracked in the system

  Background:
    Given a KiwiClient configured with a valid API key

  Scenario: Upload document with explicit title
    Given a local file at a known path
    When I call upload_document with file_path and an explicit title
    Then the document is created with the provided title
    And a DocumentSchema is returned with a document_id

  Scenario: Upload document without title defaults to filename
    Given a local file named "contract.pdf"
    When I call upload_document with file_path but no title
    Then the document is created with title "contract.pdf"
    And a DocumentSchema is returned with a document_id

  Scenario: Upload document with doc_type
    Given a local file at a known path
    When I call upload_document with file_path and doc_type "contract"
    Then the document is created with doc_type "contract"
    And a DocumentSchema is returned with a document_id

  Scenario: Upload document without doc_type is accepted
    Given a local file at a known path
    When I call upload_document with file_path but no doc_type
    Then the document is created without a doc_type
    And a DocumentSchema is returned with a document_id

  Scenario: Upload document with external_id maps to a client system record
    Given a local file at a known path
    When I call upload_document with file_path and external_id "CRM-12345"
    Then the document is created with external_id "CRM-12345"
    And a DocumentSchema is returned with a document_id

  Scenario: Upload document without external_id is accepted
    Given a local file at a known path
    When I call upload_document with file_path but no external_id
    Then the document is created without an external_id
    And a DocumentSchema is returned with a document_id

  Scenario: Uploading a duplicate external_id raises an error
    Given a document already exists with external_id "CRM-12345"
    When I call upload_document with the same external_id "CRM-12345"
    Then an APIError is raised indicating a duplicate document

  Scenario: Invalid API key is rejected
    Given a KiwiClient configured with an invalid API key
    When I call upload_document with any file
    Then an AuthenticationError is raised
