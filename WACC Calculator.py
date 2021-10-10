import sys
import yfinance as yf
import numpy_financial as npf

def get_ticker(ticker):
    ticker = yf.Ticker(ticker)
    return ticker

def get_files(ticker):
    balance_sheet = ticker.balance_sheet.transpose()
    cf = ticker.cashflow.transpose()
    earnings = ticker.earnings
    financials = ticker.financials.transpose()
    info = ticker.info
    return balance_sheet, cf, earnings, financials, info

def fetch_files(ticker):
    return get_files(get_ticker(ticker))

def weight(info, bs):
    #market value of firm's debt/market value of firm's debt & equity
    weight_longTermDebt = bs["Long Term Debt"][0]/(bs["Long Term Debt"][0]+info["marketCap"])
    #print("Weight of Long Term Debt: ", weight_longTermDebt*100, "%")
    weight_equity = info["marketCap"]/(bs["Long Term Debt"][0]+info["marketCap"])
    #print("Weight of Long Term Debt: ", weight_equity*100, "%")
    return weight_longTermDebt, weight_equity

def ask_tax_rates():
    while True:
        try:
            n = int(input("Please enter the number of tax rates\n(For VF Corp please enter 0): "))
            return n
        except:
            pass


def taxRate(n = 0, t=[0.170, 0.1285, 0.1729]):
    tr = sum(t)/len(t)
    return tr #vfc 2021 annual report page 28; search for "effective tax rate, fiscal year 2021"

def cost_of_equity(info):
    #CAPM: r_s = r_rf + (r_m - r_rf)*b
    b = info["beta"]
    r_rf = 0.015 #10-Y treasury
    r_m = 0.092 #goldman sachs estimate, s&p 500 10-Y return stands at 13.6%
    r_s = r_rf + (r_m - r_rf) * b
    return r_s

def cost_of_LongTermDebt(vfc=0, nper=0, cr=0, fv=0, pv=0, pmtperyear=0):
    #YTM of bond
    #US918204AV00
    #par = 102, N = 5.2, CR = 0.028, v_b = 106
    vfc = int(vfc)
    if vfc == 0:
        return 0.0262
    else:
        cltd = []
        for i in range(vfc):
            print("==========Bond {}==============".format(i+1))
            nper = get_positive("nper", lower = 1)
            cr = get_positive("coupon rate (0<cr<1)", 1, 0)
            fv = get_positive("future value")
            pv = get_positive("present value")
            pmtperyear = get_positive("pmtperyear")
            nper = nper * pmtperyear
            pmt = cr/100 * pv / pmtperyear
            rate = npf.rate(nper = nper, pmt = pmt, fv = fv, pv = -pv)
            cltd.append(rate*(nper/pmtperyear))
        print(cltd)
        return sum(cltd)/len(cltd)


def get_positive(var, upper = sys.maxsize, lower = 0):
    while True:
        try:
            out = float(input("Please enter a value for {}: ".format(var)))
            if lower <= out <= upper:
                return out
        except:
            pass

def wacc(weight_debt, weight_equity, debt_cost, equity_costs, tax_rate):
    wacc = weight_debt*debt_cost*(1-tax_rate) + weight_equity*equity_costs
    print("WACC = w_d*r_d*(1-T) + w_c*r_s (Since VFC has no preferred stock)")
    print('''\n=========================================
        Weight of Long Term Debt = {wd:4f}
        Cost of Long Term Debt = {dc:4f}
        Weight of Equity = {we:4f}
        Cost of equity = {ec:4f}
        Tax rate = {tr:4f}
        =========================================
    '''.format(wd=weight_debt, dc = debt_cost,tr=tax_rate,\
               we=weight_equity, ec=equity_costs))
    print("WACC = {wd:4f}*{dc:4f}*(1-{tr:4f}) + {we:4f}*{ec:4f}".format(wd=weight_debt\
                                                            , dc = debt_cost,tr=tax_rate\
                                                           ,we=weight_equity,ec=equity_costs))
    print("WACC = {WACC:.2f}%".format(WACC=wacc*100))
    return wacc

if __name__ == "__main__":
    quit = 1
    while quit:
        try:
            ticker = (input("Please enter a stock ticker: ").upper())
            n = ask_tax_rates()
            if n == 0:
                bs, cf, e, f, info = fetch_files(ticker)
                wacc(weight(info, bs)[0], weight(info, bs)[1], cost_of_LongTermDebt()\
                     , cost_of_equity(info), taxRate())
            else:
                i = 1
                tr = []
                while i < n+1:
                    try:
                        t = float(input("Please enter tax rate {}: ".format(i)))
                        tr.append(t)
                        i += 1
                    except:
                        pass
                bs, cf, e, f, info = fetch_files(ticker)
                cltdv = int(get_positive("number of bonds to be evaluated", int(sys.maxsize), 1))
                wacc(weight(info, bs)[0], weight(info, bs)[1], cost_of_LongTermDebt(vfc = cltdv) \
                     , cost_of_equity(info), taxRate(n, tr))
        except:
            print("Something went wrong!")
