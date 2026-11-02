export default function Home() {
  return (
    <div className="stack-lg">
      <section className="hero">
        <h1>Got a medical bill you don't understand?</h1>
        <p>Compare your bill with your insurer's explanation of benefits and with the prices the hospital itself
          published. See what looks wrong, what to ask, and whether you qualify for help paying.</p>
      </section>
      <div className="tiles">
        <a className="card tile" href="#/bill">
          <h2>Check a bill</h2>
          <p className="muted">Enter your explanation of benefits (EOB) and your bill. We check the math, duplicate
            charges, Medicare coding limits, published prices and your No Surprises Act rights.</p>
          <span className="go">Start checking →</span>
        </a>
        <a className="card tile" href="#/help">
          <h2>Get help paying</h2>
          <p className="muted">Many Arizona hospitals must offer free or discounted care. Enter your household size
            and income to see what each hospital's own policy says.</p>
          <span className="go">See what you qualify for →</span>
        </a>
        <a className="card tile" href="#/prices">
          <h2>Look up a price</h2>
          <p className="muted">See what Tucson and Phoenix hospitals published for 50 common procedures: list
            price, cash price and insurer rates, with the source file for every number.</p>
          <span className="go">Search prices →</span>
        </a>
      </div>
      <section className="card stack">
        <h2>Why this exists</h2>
        <p>In a national KFF survey (2022), 41% of US adults had debt from medical or dental bills, and 44% of
          them had not paid a bill in full because they were not sure it was correct. Hospitals now publish their
          prices, but in files patients cannot open. ClearTab turns those files, and the federal billing rules, into
          plain answers.</p>
        <p className="small muted">Source: <a href="https://www.kff.org/health-costs/kff-health-care-debt-survey/"
          target="_blank" rel="noreferrer">KFF Health Care Debt Survey</a>.</p>
      </section>
    </div>
  )
}
