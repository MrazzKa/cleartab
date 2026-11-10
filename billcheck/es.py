"""Spanish text for bill check findings (same numbers and sources as the English rules).

Templates use each finding's evidence, so the Spanish text never adds or changes a number. A rule without a
template keeps its English text. Letters and phone scripts stay in English: they go to US billing offices.
"""
from billcheck.models import CheckResult, Finding

LABEL_ES = {"als": "soporte vital avanzado (ALS)", "bls": "soporte vital básico (BLS)", "ccs": "cuidados críticos (CCS)"}


def m(x) -> str:
    return "n/d" if x is None else f"${x:,.2f}"


def es(f: Finding) -> tuple[str, str, str] | None:
    e, n = f.evidence, f.lines
    ln = n[0] if n else ""
    r = f.rule
    if r == "balance_over_eob":
        owed, paid, bal = e.get("eob_you_owe"), e.get("already_paid"), e.get("bill_balance")
        if paid and f.amount_at_stake and abs(f.amount_at_stake - paid) < 0.03:
            return ("Es posible que no le hayan descontado un pago que ya hizo",
                    f"Su EOB dice que debe {m(owed)} en total. Usted ya pagó {m(paid)}, así que la factura debería "
                    f"mostrar {m(max(owed - paid, 0))}, pero le cobra {m(bal)}.",
                    "No pague otra vez. Llame a la oficina de facturación, dé la fecha y el monto de su pago (un recibo "
                    "o el estado de cuenta de su tarjeta ayuda) y pida que lo apliquen a esta cuenta.")
        return (f"La factura le cobra {m(f.amount_at_stake)} más de lo que su EOB dice que debe",
                f"Su EOB dice que debe {m(owed)}" + (f", menos {m(paid)} que ya pagó" if paid else "")
                + f". La factura le cobra {m(bal)}.",
                "No pague la diferencia todavía. Llame a la oficina de facturación del proveedor con su EOB, pida que "
                "la factura coincida con el EOB y pida una factura detallada.")
    if r == "balance_matches_eob":
        return ("La factura coincide con su EOB", f.explanation.replace("Both say you owe", "Ambos dicen que debe"), "")
    if r == "balance_under_eob":
        return ("La factura es menor que su parte según el EOB",
                "Puede llegar otra factura más adelante, o se aplicó un ajuste.",
                "Guarde el EOB y pague lo que pide la factura; revise el próximo estado de cuenta.")
    if r == "no_eob_yet":
        return ("Espere su Explicación de Beneficios (EOB) antes de pagar",
                "Su aseguradora le envía un EOB después de procesar la reclamación. Ahí dice cuánto debe. Hasta "
                "entonces, la factura puede no incluir lo que pagará su seguro.",
                "Busque el EOB en la aplicación o el sitio web de su aseguradora, o llame al número de su tarjeta del "
                "seguro. Si el proveedor nunca facturó a su seguro, déle los datos de su tarjeta.")
    if r == "bill_line_not_on_eob":
        return (f"{len(n)} cargo(s) de la factura no aparecen en su EOB",
                "Es posible que su aseguradora nunca haya recibido estos servicios, o que estén en otra reclamación.",
                "Pregunte al proveedor si los facturó a su seguro. Si no, déle los datos de su tarjeta y pida que "
                "envíen la reclamación antes de pagar.")
    if r == "duplicate_line":
        return (f"Posible cargo duplicado: {e.get('service')} aparece {e.get('times')} veces",
                f"El mismo servicio, fecha y monto ({m(e.get('amount'))}) aparece {e.get('times')} veces. A veces es "
                "correcto (por ejemplo, dos pruebas distintas); muchas veces es un error de facturación.",
                "Pregunte a la oficina de facturación si recibió este servicio más de una vez.")
    if r == "mue_units":
        return (f"{e.get('code')}: {e.get('units')} unidades; el límite de Medicare es {e.get('limit')}",
                f"CMS fija un máximo de unidades para este código ({e.get('limit')}). Los cargos por encima casi nunca "
                "se pagan y a menudo son un error al capturar datos.",
                "Pida a la oficina de facturación que confirme el número de unidades y corrija la factura si hace falta.")
    if r == "ncci_pair":
        a, b = e.get("column_1"), e.get("column_2")
        return (f"{a} y {b} normalmente no se facturan juntos",
                f"CMS considera {b} parte de {a} cuando ambos se hacen el mismo día.",
                f"Pregunte a la oficina de facturación por qué {b} se cobra aparte de {a}.")
    if r == "allowed_vs_published":
        return (f"{e.get('code')}: el monto permitido es distinto de las tarifas publicadas por el hospital",
                f"{e.get('hospital')} publicó tarifas para su plan de {m(e.get('published_min'))} a "
                f"{m(e.get('published_max'))}; su EOB permitió {m(e.get('allowed_per_unit'))}.",
                "Pregunte a su aseguradora qué tarifa de contrato se aplicó a este servicio.")
    if r == "allowed_matches_published":
        return (f"{e.get('code')}: el monto permitido está dentro de las tarifas publicadas",
                f"{e.get('hospital')} publicó tarifas de {m(e.get('published_min'))} a {m(e.get('published_max'))}; "
                f"su EOB permitió {m(e.get('allowed_per_unit'))}.", "")
    if r == "plan_balance_left":
        lines = [x.replace("Deductible", "Deducible").replace("Out-of-pocket limit", "Límite de gastos de bolsillo")
                 .replace("in network", "dentro de la red").replace("out of network", "fuera de la red")
                 .replace("family", "familia").replace("individual", "individual").replace(" used, ", " usados, ")
                 .replace(" of ", " de ").replace(" left.", " disponibles.") for x in e.get("lines", [])]
        return ("Lo que queda de su deducible y de su límite de gastos de bolsillo",
                " ".join(lines) + " Hasta cubrir el deducible, normalmente paga todo el monto permitido; después, "
                "solo copagos o coseguro. Al llegar al límite de gastos de bolsillo, la atención cubierta dentro de "
                "la red le cuesta $0 hasta que termine el año del plan.",
                "Guarde este EOB: el siguiente debe mostrar estas cifras subiendo, nunca bajando.")
    if r == "plan_balance_math":
        return ("Las cifras del saldo del plan no cuadran",
                f"El EOB muestra un límite de {m(e.get('limit'))} con {m(e.get('used'))} usados, pero dice que "
                f"quedan {m(e.get('remaining'))}.",
                "Pida a su aseguradora un estado de lo que ha contado para su deducible y su límite este año.")
    if r == "plan_balance_over":
        return ("Se cuenta como usado más que el límite",
                f"El EOB cuenta {m(e.get('used'))} para un límite de {m(e.get('limit'))}.",
                "Pida a su aseguradora que revise lo que se cuenta para este límite.")
    if r == "oop_met_still_owe":
        return ("Llegó a su límite de gastos de bolsillo, pero esta reclamación le pide pagar",
                f"El saldo del plan muestra el límite cubierto, pero este EOB dice que debe {m(e.get('you_owe'))}.",
                "Pregunte a su aseguradora si esta reclamación se procesó antes de llegar al límite y si debe "
                "reprocesarse.")
    if r in ("er_rate_matches", "er_rate_over", "er_rate_within"):
        lo, hi = e.get("published_min"), e.get("published_max")
        rango = m(lo) if lo == hi else f"de {m(lo)} a {m(hi)}"
        if r == "er_rate_matches":
            return ("Visita a urgencias: el monto permitido coincide con la tarifa publicada por el hospital",
                    f"{e.get('hospital')} publica {m(e.get('allowed'))} para {e.get('insurer')} "
                    f"(plan {', '.join(e.get('plans', []))}, {e.get('methodology', '')}). Su EOB permitió "
                    f"{m(e.get('allowed'))}: la aseguradora aplicó la tarifa de contrato publicada.", "")
        if r == "er_rate_over":
            return ("Visita a urgencias: el monto permitido es mayor que las tarifas publicadas",
                    f"{e.get('hospital')} publica tarifas de urgencias para {e.get('insurer')} {rango}. Su EOB "
                    f"permitió {m(e.get('allowed'))}. Puede que se haya usado otro contrato u otro nivel de visita.",
                    "Pregunte a su aseguradora qué tarifa y qué nivel de visita se aplicaron, y pida al hospital la "
                    "factura detallada con el código CPT de la visita.")
        return ("Visita a urgencias: el monto permitido está dentro de las tarifas publicadas",
                f"{e.get('hospital')} publica tarifas de urgencias para {e.get('insurer')} {rango}, según el plan "
                f"y el nivel de visita. Su EOB permitió {m(e.get('allowed'))}.", "")
    if r == "self_pay_over_cash":
        return (f"{e.get('code')}: le cobraron más que el precio en efectivo publicado",
                f"{e.get('hospital')} publica un precio con descuento en efectivo de {m(e.get('published_cash'))}. "
                f"Le cobraron {m(e.get('billed_per_unit'))}.",
                "Pida al hospital que aplique su precio con descuento en efectivo publicado.")
    if r == "self_pay_at_cash":
        return (f"{e.get('code')}: le cobraron el precio en efectivo publicado o menos",
                f"Precio en efectivo publicado {m(e.get('published_cash'))}; cobrado {m(e.get('billed_per_unit'))}.", "")
    if r == "billed_over_gross":
        return ("El cargo es mayor que el precio de lista publicado por el hospital",
                "Lo que usted paga depende del monto permitido, no del cargo, pero puede preguntar por qué.", "")
    if r in ("eob_line_sum", "eob_owe_sum", "eob_total"):
        return (f"Las cifras del EOB no cuadran (línea {ln})" if ln else "Las cifras del EOB no cuadran",
                "El monto permitido debería ser igual a lo que pagó el plan más su copago, deducible y coseguro.",
                "Revise que copió bien la línea. Si es así, pida a su aseguradora que le explique la diferencia.")
    if r == "eob_allowed_over_billed":
        return ("El monto permitido es mayor que el cargo", "Normalmente la aseguradora permite lo mismo o menos.", "")
    if r == "eob_denied":
        return (f"Su aseguradora negó {len(n)} línea(s)",
                "Una negación es una decisión que usted puede apelar. El aviso debe decir por qué y cómo apelar. A "
                "menudo se debe a falta de información: una referencia, una autorización previa o los datos de su seguro.",
                "Llame a su aseguradora y pida el motivo por escrito; pida al proveedor que corrija y reenvíe la "
                "reclamación. No pague el monto negado mientras tanto.")
    if r == "eob_pending":
        return ("Algunas líneas todavía se están procesando",
                "Hasta que la aseguradora termine, nadie sabe cuál será su parte.",
                "Espere el EOB final antes de pagar estos servicios.")
    if r == "nsa_emergency":
        return ("La atención de emergencia está protegida contra facturas sorpresa",
                "En una emergencia, un proveedor fuera de la red no puede cobrarle más que su copago, coseguro o "
                "deducible dentro de la red.",
                "Si le cobraron más, llame a la línea de ayuda No Surprises al 1-800-985-3059.")
    if r == "nsa_facility_provider":
        return ("¿Médico fuera de la red en un hospital dentro de la red?",
                "Si este médico lo atendió en un hospital o centro quirúrgico dentro de su red, la ley No Surprises "
                "normalmente limita lo que paga a su parte dentro de la red, salvo que haya firmado un aviso y "
                "consentimiento.",
                "Pregunte al proveedor si usted firmó un formulario de aviso y consentimiento y pida una copia.")
    if r == "nsa_air_ambulance":
        return ("Las facturas de ambulancia aérea están protegidas",
                "Por ambulancia aérea fuera de la red, no debe pagar más que su parte dentro de la red.",
                "Si le cobraron más, llame al 1-800-985-3059.")
    if r == "nsa_ground_ambulance":
        return ("Las ambulancias terrestres no tienen la protección federal",
                "La ley No Surprises no cubre ambulancias terrestres. En Arizona, sin embargo, el estado fija cuánto "
                "puede cobrar cada servicio de ambulancia.",
                "Pida una factura detallada y revise la tarifa aprobada por ADHS para su servicio de ambulancia.")
    if r == "gfe_missing":
        return ("¿Sin seguro o paga usted? Puede pedir una estimación de buena fe",
                "Si programa atención y no usa seguro, el proveedor debe darle una estimación de buena fe. Si la "
                "factura supera la estimación por $400 o más, puede disputarla.",
                "Para la próxima vez, pida una estimación de buena fe por escrito al programar la cita.")
    if r == "gfe_dispute":
        return (f"La factura es {m(f.amount_at_stake)} mayor que su estimación de buena fe",
                "Si un proveedor cobra $400 o más por encima de su estimación de buena fe, un paciente sin seguro "
                "puede iniciar el proceso federal de disputa dentro de los 120 días de la primera factura. Cuesta "
                "$25, que se descuentan de lo que debe si usted gana.",
                "Guarde la estimación y la factura. Inicie la disputa en cms.gov/medical-bill-rights o llame al "
                "1-800-985-3059.")
    if r == "gfe_within":
        return ("La factura está dentro de $400 de su estimación de buena fe", "", "")
    if r == "itemized_bill":
        return ("Pida una factura detallada",
                "Una factura resumida no dice por qué es cada cargo. La factura detallada muestra cada servicio con su "
                "código (CPT o HCPCS), fecha y unidades.",
                "Pida a la oficina de facturación: 'Please send me an itemized bill with CPT or HCPCS codes.'")
    if r == "facility_or_provider":
        return ("¿Es una factura del hospital o del médico?",
                "Los hospitales y los médicos suelen enviar facturas separadas, desde oficinas distintas. Le "
                "preguntarán cuál de las dos es.",
                "Busque en la factura 'professional', el nombre de un grupo médico u 'hospital services'.")
    if r == "ambulance_over_rate":
        return ("La factura de ambulancia supera la tarifa aprobada por Arizona",
                f"El Departamento de Salud de Arizona (ADHS) aprobó para {e.get('company', 'este servicio')} una "
                f"tarifa base ALS de {m(e.get('als'))}" + (f", BLS de {m(e.get('bls'))}" if e.get("bls") else "")
                + f" y {m(e.get('per_mile'))} por milla. La ley de Arizona (A.R.S. 36-2239) prohíbe cobrar más.",
                "Pida a la compañía de ambulancia que corrija el cobro a la tarifa aprobada por ADHS. Si no lo hace, "
                "puede presentar una queja ante la Oficina de EMS de ADHS.")
    if r == "ambulance_within_rate":
        return ("La factura de ambulancia está dentro de la tarifa aprobada por Arizona", "", "")
    if r == "ambulance_no_transport":
        return ("No lo llevaron al hospital",
                "En Arizona, sin traslado solo se puede cobrar la tarifa base de soporte vital avanzado si usted "
                "recibió esa atención. Si rechazó la atención o el traslado, la ley permite que el servicio no cobre "
                "(A.R.S. 36-2239(K)).",
                "Pregunte por qué atención le cobraron. Si rechazó la atención, pida que no le cobren según A.R.S. "
                "36-2239(K).")
    if r == "network_discount":
        return (f"El proveedor descontó {m(e.get('discount'))} de su cargo de {m(e.get('billed'))}",
                "Es el descuento que negoció su aseguradora. Un proveedor de su red aceptó cobrar el monto permitido, "
                "así que no puede cobrarle a usted ese descuento (esto se llama facturación del saldo).",
                "Si una factura de este proveedor le cobra más de lo que dice el EOB, no pague la diferencia; llame "
                "a la oficina de facturación con el EOB.")
    if r == "eob_zero_allowed":
        return (f"Línea(s) {', '.join(map(str, n))}: la aseguradora permitió $0",
                "La aseguradora no permitió nada por este servicio, pero no lo negó, y usted no debe nada por él. "
                "Normalmente significa que está incluido en el pago de otro servicio de la misma reclamación, como "
                "una extracción de sangre incluida en una visita de emergencia.",
                "No debe nada por esta línea. Si una factura la cobra por separado, pregunte por qué.")
    if r == "oop_max_met":
        return ("Alcanzó su máximo de gastos de bolsillo",
                "El EOB dice que ya alcanzó su máximo de gastos de bolsillo de este año del plan. Desde entonces su "
                "plan paga el 100% de la atención cubierta dentro de la red hasta que termine el año del plan: sin "
                "más deducible, copagos ni coseguro.",
                "Revise cada factura y EOB posterior de este año del plan. Si le cobran un copago, deducible o "
                "coseguro por atención cubierta dentro de la red, pregunte a la aseguradora por qué.")
    if r == "eob_owe_zero":
        return ("Usted debe $0 por esta reclamación",
                "Los descuentos y pagos de su plan cubren todo el cargo. El EOB no es una factura, pero el proveedor "
                "debe seguirlo.",
                "Guarde este EOB. Si el proveedor le envía una factura por estos servicios, no la pague: llame a la "
                "oficina de facturación y dé el número de reclamación del EOB.")
    return None


HEADLINES = {
    "likely_errors": lambda n, amt: f"Encontramos {n} error(es) probable(s)" + (f" por hasta {m(amt)}." if amt else "."),
    "questions": lambda n, _amt: f"{n} cosa(s) que preguntar antes de pagar.",
    "looks_right": lambda _n, _amt: "Nada de lo que ingresó parece incorrecto.",
    "not_enough_data": lambda _n, _amt: "Todavía no pudimos comparar su factura con nada.",
}


def to_spanish(res: CheckResult) -> CheckResult:
    for f in res.findings:
        t = es(f)
        if t:
            f.title, f.explanation, f.action = t
    s = res.summary
    n = s.counts.get("error", 0) if s.verdict == "likely_errors" else s.counts.get("warning", 0)
    s.headline = ("Su EOB dice que debe $0 por esta reclamación." if s.headline.startswith("Your EOB says you owe $0")
                  else HEADLINES[s.verdict](n, s.amount_at_stake))
    res.disclaimer = ("ClearTab compara lo que usted ingresa con reglas y precios publicados. No es asesoría legal ni "
                      "médica; una alerta significa 'pregunte por esto', no 'esto está mal'. La carta está en inglés "
                      "porque va dirigida a la oficina de facturación.")
    return res
