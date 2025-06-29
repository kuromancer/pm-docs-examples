from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs, PartialCreateOrderOptions, MarketOrderArgs, OrderScoringParams, OpenOrderParams
from py_clob_client.order_builder.constants import BUY, SELL
from py_clob_client.exceptions import PolyApiException
from math import floor

funder = "" #The Funder is the adress as seen on your Polymarket profile.
host = "https://clob.polymarket.com"
key = "" #This is your private key. See above for details 
chain_id = 137
signature_type = 1

client = ClobClient(
host,               # the polymarket host
key=key,            # your private key exported from magic/polymarket
chain_id=chain_id,  # 137
signature_type=1,   # this type of config requires this signature type
funder=funder) # this is your polymarket public address (where you send the usdc)

client.set_api_creds(client.create_or_derive_api_creds())


#In production you absolutely need try/catch blocks here but for the purposes of simplicity we're ignoring that neccesity for now. 
def buy_sell_limit_order(action: str, tokenID: str, numShares: int, price: float = .99, neg_risk_status: bool = False):
    if action == 'BUY':
        order_args = OrderArgs(
            token_id=tokenID,
            side='BUY',
            size=floor(numShares),
            price=price
            )
        signed_order = client.create_order(order_args, PartialCreateOrderOptions(neg_risk=neg_risk_status))
    elif action == 'SELL':
        order_args = OrderArgs(
            token_id=tokenID,
            side='SELL',
            price=price,#hardcode for sell
            size=numShares #will be shares in this case
                        )
        signed_order = client.create_order(order_args, PartialCreateOrderOptions(neg_risk=neg_risk_status))
    else: 
        print(f"Invalid action. Action recieved: {action}")
        return


    #NotEnough balance/allowance can mean that you dont have enough shares 
    #invalid sig can mean its negrisk or your funder is 
    resp = client.post_order(signed_order)
    print(f"Order Response: {resp}")


buy_sell_limit_order('BUY',"55339638397443112919791846485253629869798811464400272253569648598507361954673",5,price=.01,neg_risk_status=False)