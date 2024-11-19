from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
import matplotlib.pyplot as plt
import io
from datetime import date
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow only GET and POST methods
    allow_headers=["*"],  # Allow specific headers
)




# Define a request body model
class StockRequest(BaseModel):
    ticker: str
    years: int
    plot_type: str  # 'ema' or 'high-low'
    start_date: str = None
    end_date: str = None 

@app.post("/stock-plots/")
async def get_stock_plots(stock: StockRequest): 
    try:
        today = date.today()

        # Ensure START_DATE and END_DATE are defined properly
        if stock.start_date and stock.end_date:
            START_DATE = stock.start_date
            END_DATE = stock.end_date
        else:
            END_DATE = today.isoformat()
            START_DATE = date(today.year - stock.years, today.month, today.day).isoformat()

        # Fetch stock data
        data = yf.download(stock.ticker, start=START_DATE, end=END_DATE)

        # Check if data is empty
        if data.empty:
            raise HTTPException(status_code=404, detail="Stock data not found")

        # Conditional plot generation based on the 'plot_type' parameter
        if stock.plot_type == "ema":
            # Calculate Exponential Moving Averages (EMA)
            data['EMA-20'] = data['Close'].ewm(span=20, adjust=False).mean()
            data['EMA-50'] = data['Close'].ewm(span=50, adjust=False).mean()
            data['EMA-200'] = data['Close'].ewm(span=200, adjust=False).mean()

            # Exponential Moving Average Graph
            plt.figure(figsize=(8, 4))
            plt.plot(data['EMA-20'], label="EMA for 20 days")
            plt.plot(data['EMA-50'], label="EMA for 50 days")
            plt.plot(data['EMA-200'], label="EMA for 200 days")
            plt.plot(data['Adj Close'], label="Close")
            plt.title(f'Exponential Moving Average for {stock.ticker}')
            plt.ylabel('Price (in USD)')
            plt.xlabel("Time")
            plt.legend()
            plt.tight_layout()

            # Save EMA plot to a BytesIO object
            plot = io.BytesIO()
            plt.savefig(plot, format="png")
            plot.seek(0)  # Reset pointer to the beginning
            return StreamingResponse(plot, media_type="image/png")

        elif stock.plot_type == "high-low":
            # High vs Low Graph
            plt.figure(figsize=(8, 4))
            plt.plot(data['Low'], label="Low", color="indianred")
            plt.plot(data['High'], label="High", color="mediumseagreen")
            plt.ylabel('Price (in USD)')
            plt.xlabel("Time")
            plt.title(f"High vs Low of {stock.ticker}")
            plt.tight_layout()
            plt.legend()

            # Save High vs Low plot to a BytesIO object
            plot = io.BytesIO()
            plt.savefig(plot, format="png")
            plot.seek(0)  # Reset pointer to the beginning
            return StreamingResponse(plot, media_type="image/png")

        else:
            raise HTTPException(status_code=400, detail="Invalid plot_type. Use 'ema' or 'high-low'.")

    except Exception as e:
        # Log the error and return a 500 status code with the error message
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
        
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
