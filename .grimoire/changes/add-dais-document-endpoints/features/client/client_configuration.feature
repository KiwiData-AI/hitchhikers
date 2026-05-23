Feature: Client configuration
  As a developer installing the hitchhikers SDK
  I want to configure the API endpoint, API key, and retry behaviour at construction time
  So that I can target different environments and tune resilience without modifying code

  Scenario: Construct client with API key only
    When I construct KiwiClient with api_key "my-key"
    Then requests are authenticated with X-API-Key header "my-key"
    And the base URL defaults to "https://api.neolicense.ai"

  Scenario: Construct client with custom base URL
    When I construct KiwiClient with api_key "my-key" and base_url "https://staging.neolicense.ai"
    Then requests target "https://staging.neolicense.ai"

  Scenario: Client retries on transient 5xx errors
    Given the API returns a 503 error once then succeeds
    When I make any API request
    Then the client retries and returns the successful response
    And the caller receives no error

  Scenario: Client retries on network errors
    Given the API connection times out once then succeeds
    When I make any API request
    Then the client retries and returns the successful response

  Scenario: Client raises after exhausting default retry limit
    Given the API returns 5xx errors on all attempts
    When I make any API request
    Then an APIError is raised after 2 retries are exhausted

  Scenario: Construct client with custom retry count
    When I construct KiwiClient with api_key "my-key" and max_retries 5
    Then the client retries up to 5 times on transient errors before raising

  Scenario: Client does not retry on 4xx errors
    Given the API returns a 404 response
    When I make an API request
    Then a NotFoundError is raised immediately without retrying
