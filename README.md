
# Shorties

A robust, extensible URL shortener — engineered for clarity, reliability, and future innovation.

## Overview
Shorties(shortened urls) is a thoughtfully designed URL shortening service, built with maintainability and scalability in mind. Its primary function is to transform lengthy URLs into concise, shareable links, while providing a solid foundation for advanced features and enhancements. It's the next Big Think coming out of Inwood, NYC('The silicon-valley of the northeast! So i have heard')

The project roadmap includes a unique, innovative twist (currently under wraps) that will differentiate Shorties from conventional solutions. Stay tuned for upcoming announcements.

## Features
- Deterministic, collision-resistant URL shortening
- Intuitive, developer-friendly API
- Comprehensive error handling and input validation
- Designed for extensibility and easy integration
- Clear, maintainable codebase with best practices in mind
- Additional features and a signature twist coming soon

## Getting Started

To get up and running with Shorties, follow these steps:

1. **Clone the repository:**
    ```sh
    git clone git@github.com:iamserda/shorties.git
    cd shorties
    ```

2. **Install Poetry:**
    - **Linux:**
      ```sh
      sudo apt install poetry
      ```
    - **macOS:**
      ```sh
      brew install pipx
      pipx install poetry
      ```

3. **Install project dependencies:**
    Ensure you are in the project root (where `pyproject.toml` is located):
    ```sh
    poetry env activate
    poetry install
    ```

4. **Run the application:**
    Further instructions for running the service will be provided in future updates as config is subject to change to be more autonomous for deployment.
    For now, we will use:
    ```sh
    poetry run python src/app/main.py
    ```

## Contributing

Contributions are welcome and encouraged. If you have ideas for the upcoming twist, architectural improvements, or feature requests, please open an issue or submit a pull request. All contributions should adhere to clean code principles and include relevant documentation and tests where applicable.

## License

This project is licensed under the MIT License.
