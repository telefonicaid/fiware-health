# -*- coding: utf-8 -*-

Feature: sanity check status

  As FIWARE user
  I want to retrieve the public sanity check status web portal


  Scenario: Get public list with region status
    Given the web server running properly
    When  I launch get operation
    Then  I receive a HTTP "200" OK response


  @selenium
  Scenario: Get public list with region status
    Given the web server running properly
    When  I launch get operation
    Then  the response title contains Sanity check status
