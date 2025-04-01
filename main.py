"""sd"""
import threading
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
from xrpl.clients import WebsocketClient
from xrpl.models.requests import Subscribe
from xrpl.utils import drops_to_xrp


# XRPL WebSocket server
WS_URL = "wss://xrpl.ws/"

# Initialize Dash app with external stylesheet
app = dash.Dash(
    __name__,
    external_stylesheets=[
        "https://cdnjs.cloudflare.com/ajax/libs/skeleton/2.0.4/skeleton.min.css"
    ],
)

app.layout = html.Div(
    style={
        "backgroundColor": "black",
        "color": "white",
        "minHeight": "100vh",
        "padding": "20px",
    },
    children=[
        html.H1("Whale watcher", style={"textAlign": "center", "color": "white"}),
        dash_table.DataTable(
            id="transaction-table",
            columns=[
                {"name": "Sequence", "id": "Sequence"},
                {"name": "Sender", "id": "Sender", "presentation": "markdown"},
                {"name": "Recipient", "id": "Recipient", "presentation": "markdown"},
                {"name": "Amount (XRP)", "id": "Amount"},
            ],
            data=[],
            style_table={"overflowX": "auto"},
            markdown_options={"html": True},
            style_header={
                "backgroundColor": "#222",
                "color": "white",
                "fontWeight": "bold",
            },
            style_data={
                "backgroundColor": "black",
                "color": "white",
            },
        ),
        html.H2(
            "Highest Transactions", style={"textAlign": "center", "color": "white"}
        ),
        dash_table.DataTable(
            id="highest-transactions-table",
            columns=[
                {"name": "Sequence", "id": "Sequence"},
                {"name": "Sender", "id": "Sender", "presentation": "markdown"},
                {"name": "Recipient", "id": "Recipient", "presentation": "markdown"},
                {"name": "Amount (XRP)", "id": "Amount"},
            ],
            data=[],
            style_table={"overflowX": "auto"},
            markdown_options={"html": True},
            style_header={
                "backgroundColor": "#222",
                "color": "white",
                "fontWeight": "bold",
            },
            style_data={"backgroundColor": "black", "color": "white"},
            style_data_conditional=[
                {
                    "if": {"filter_query": "{Amount} > 5000"},
                    "backgroundColor": "red",
                    "color": "white",
                    "fontWeight": "bold",
                    "textAlign": "center",
                },
                {
                    "if": {"filter_query": "{Amount} > 1000 && {Amount} <= 4999"},
                    "backgroundColor": "blue",
                    "color": "white",
                    "fontWeight": "bold",
                    "textAlign": "center",
                },
            ],
        ),
        html.Br(),
        # Slider in a Block
        html.Div(
            style={
                "backgroundColor": "#222",
                "border": "2px solid white",
                "padding": "20px",
                "borderRadius": "10px",
                "textAlign": "center",
                "margin": "20px auto",
                "width": "50%",
            },
            children=[
                html.Label(
                    "Filter Transactions by Amount (XRP)",
                    style={"color": "white", "fontSize": "18px"},
                ),
                dcc.Slider(
                    id="amount-slider",
                    min=100,
                    max=100000,
                    step=100,
                    value=100,
                    marks={
                        i: str(i) for i in range(100, 100001, 19800)
                    },  # Marks at every 19,800
                    tooltip={"placement": "bottom", "always_visible": True},
                ),
            ],
        ),
        dcc.Interval(id="interval-component", interval=5000, n_intervals=0),
    ],
)

# Store transaction data
tx_data = []
highest_tx_data = []


def process_transaction(transaction):
    """asdasd"""
    try:
        if transaction.get("tx_json"):
            tx = transaction["tx_json"]
            if tx.get("TransactionType") == "Payment":
                sender = tx["Account"]
                recipient = tx["Destination"]
                sequence = tx["LastLedgerSequence"]
                amount = tx.get("DeliverMax") or tx.get("Amount")

                # Skip transactions if sender is "X" or recipient is "Y"
                if sender == "X" or recipient == "Y":
                    return

                if isinstance(amount, str) and recipient != sender:
                    amount = float(drops_to_xrp(amount))
                    if amount >= 10:
                        tx_entry = {
                            "Sequence": sequence,
                            "Sender": f"<a href='https://xrpscan.com/account/{sender}' target='_blank'> {sender}</a>",
                            "Recipient": f"<a href='https://xrpscan.com/account/{recipient}' target='_blank'> {recipient}</a>",
                            "Amount": amount,
                        }
                        tx_data.append(tx_entry)
                        tx_data[:] = tx_data[-5:]  # Keep only last 5 transactions

                        # Maintain highest transactions list
                        highest_tx_data.append(tx_entry)
                        highest_tx_data.sort(key=lambda x: x["Amount"], reverse=True)
                        highest_tx_data[:] = highest_tx_data[:5]  # Keep only top 5
    except Exception:
        pass


def run_websocket():
    """sdfsdf"""
    with WebsocketClient(WS_URL) as client:
        sub_request = Subscribe(streams=["transactions"])
        client.send(sub_request)
        for message in client:
            process_transaction(message)


# Run WebSocket in a separate thread
threading.Thread(target=run_websocket, daemon=True).start()


@app.callback(
    [Output("transaction-table", "data"), Output("highest-transactions-table", "data")],
    [Input("interval-component", "n_intervals"), Input("amount-slider", "value")],
)
def update_tables(_, min_amount):
    """asdasd"""
    min_amount = float(min_amount)

    # Filter the transactions based on the slider amount
    filtered_tx_data = [tx for tx in tx_data if tx["Amount"]]
    filtered_highest_tx_data = [
        tx for tx in highest_tx_data if tx["Amount"] >= min_amount
    ]

    return filtered_tx_data, filtered_highest_tx_data


if __name__ == "__main__":
    app.run(debug=False)
