Feature: List documents
  As a developer integrating with the Kiwi DAIS API
  I want to list and filter documents in the system
  So that I can find documents relevant to my workflow

  Background:
    Given a KiwiClient configured with a valid API key

  Scenario: List all documents with default pagination
    When I call list_documents()
    Then the response contains a list of documents and a total count
    And the default limit is 100 and offset is 0

  Scenario: Filter documents by doc_type
    When I call list_documents with doc_type "contract"
    Then only documents of type "contract" are returned

  Scenario: Filter documents by business_partner_id
    When I call list_documents with a valid business_partner_id
    Then only documents linked to that business partner are returned

  Scenario: Filter documents by internal_legal_entity_id
    When I call list_documents with a valid internal_legal_entity_id
    Then only documents for that legal entity are returned

  Scenario: Filter documents by date range
    When I call list_documents with start_date_gte "2024-01-01" and end_date_lte "2024-12-31"
    Then only documents with dates within that range are returned

  Scenario: Paginate results
    When I call list_documents with limit 10 and offset 20
    Then results are limited to 10 items starting at offset 20

  Scenario: Invalid API key is rejected
    Given a KiwiClient configured with an invalid API key
    When I call list_documents()
    Then an AuthenticationError is raised
