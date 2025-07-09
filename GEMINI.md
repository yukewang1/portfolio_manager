# Portfolio Manager Plan

This document outlines the plan and instructions for building the portfolio management tool.

## High-Level Design

The program is a Python-based Command-Line Interface (CLI) tool designed to consolidate investment accounts, analyze them against a target allocation, and provide clear rebalancing instructions.

### Core Features:
- **Unified Portfolio View:** See all accounts from multiple brokers in one place.
- **Target-Based Rebalancing:** Generate buy/sell orders based on a user-defined target allocation.
- **Multi-Currency Management:** Normalize all assets and cash into a single `reporting_currency` for accurate calculations.
- **Configurable Asset Skipping:** Allow certain tickers to be ignored during rebalancing.
- **Allocation Drift Score & Threshold:** Calculate a single score for how "off-target" the portfolio is and use a threshold to decide when to rebalance.

## User Instructions
- The project should be written in Python.
- A virtual environment must be used. The developer uses `asdf` for Python version management.
- Do not implement specific broker connectors initially. Focus on the core framework, models, and logic.
