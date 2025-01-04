---

# Deliveroo Automated Ordering System

## Quick Start Guide

This project automates placing orders on Deliveroo using Deliveroo's API. It leverages proxy support, error handling, item collection, basket management, and payment processing.

### Prerequisites

Before running the app, ensure you have the following installed:

- **Python 3.6+**
- **Virtual Environment (optional but recommended)**

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Install Dependencies

Ensure you have `pip` installed and use it to install the required Python dependencies from `requirements.txt`.

```bash
pip install -r requirements.txt
```

### 3. Set Up the Environment Variables

Create a `.env` file in the root of your project directory and add your credentials and configuration variables as shown below:

#### Example `.env` file:

```env
# Cridetails of Deliveroo App
AUTHORIZATION="Basic OTY0MzVhSNUxXd..."
X_ROO_GUID="A61422A9-563B-4F6B-BAC7-C0907B9E1506"
X_ROO_STICKY_GUID="22430b47-a29c-4201-8216-358081bd974f"
TELEGRAM_CHAT_ID="-456..."
TELEGRAM_MESSAGE_TEMPLATE="Some message to telegram"
TELEGRAM_BOT_TOKEN="bot7338..."

# Proxy Settings (Optional)
USE_PROXY="False"
HOST="193.41.39.48"
PORT="50100"
LOGIN="sharshenaliev2003"
PASSWORD="t4II4h8Byc"

# Deliveroo Restaurant ID
RESTAURANT_ID="636210"
```

> **Note:** Replace placeholder values with your actual credentials.

### 4. Running the App

Once everything is set up, run the application by executing:

```bash
python main.py
```

The app will start the ordering process and proceed through various stages:

1. **CHECK_IP:** Verifies the proxy setup.
2. **CLEAN_BASKET:** Clears the basket (if any).
3. **COLLECTING_PRODUCTS:** Collects items from the queue and adds them to the basket.
4. **CHECKOUT:** Initiates payment plan creation.
5. **EXECUTE_PAYMENT:** Executes the payment process.
6. **HALAS:** Ends the flow.

### 5. Optional Proxy Support

If you wish to use a proxy, set `USE_PROXY="True"` in the `.env` file and provide the proxy credentials (host, port, username, and password).

### Telegram Notifications

If you wish to receive Telegram notifications for certain events (such as web challenges), make sure to fill in your `TELEGRAM_CHAT_ID`, `TELEGRAM_MESSAGE_TEMPLATE`, and `TELEGRAM_BOT_TOKEN` in the `.env` file.

### 6. Error Handling

- **Rate Limiting (429):** The app will automatically wait and retry in case of rate limits.
- **Unauthorized Access (401):** Make sure your API credentials are correct.
- **Payment Declined:** The app will notify you if there is an issue with the payment process.

---

### File Overview

- **`app.py`**: Main application logic handling API calls, basket management, payment, etc.
- **`requirements.txt`**: Python dependencies required to run the app.
- **`graphql/`**: Directory containing GraphQL queries used by the app (e.g., `clear_basket.graphql`, `addBasket.graphql`, etc.).
- **`.env`**: Environment file where sensitive information like API keys, restaurant ID, and proxy credentials are stored.

### Dependencies

Ensure the following Python packages are installed:

```txt
colorama==0.4.6
python-dotenv==1.0.1
requests==2.32.3
```

### 7. Troubleshooting

- **Error: `Proxy error`**  
  Check your proxy settings in the `.env` file or try setting `USE_PROXY="False"` to bypass proxy configuration.

- **Error: `Payment declined`**  
  Double-check payment settings, ensure the payment method is valid, or try changing it.

---

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

--- 

This should help you quickly get started with your Deliveroo automated ordering system!
