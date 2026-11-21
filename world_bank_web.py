import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import numpy as np
    try:
        import pingouin as pg
    except ImportError:
        # the browser version of Python has no pingouin: same numbers with scipy
        from scipy import stats as _st

        class _Pg:
            @staticmethod
            def corr(x, y, method="pearson"):
                _f = _st.spearmanr if method == "spearman" else _st.pearsonr
                _res = _f(x, y)
                _r = float(_res[0])
                _p = float(_res[1])
                _n = len(x)
                _z = np.arctanh(min(max(_r, -0.999999), 0.999999))
                _se = 1 / np.sqrt(_n - 3)
                _ci = [float(np.tanh(_z - 1.96 * _se)), float(np.tanh(_z + 1.96 * _se))]
                return pd.DataFrame({"n": [_n], "r": [_r], "CI95": [_ci], "p_val": [_p]})

        pg = _Pg()

    return alt, mo, np, pd, pg


@app.cell
def _(pd):
    base_url = "https://docs.google.com/spreadsheets/d/"
    doc_id = "1YY5iwL8J53umfHMNhJd1m-MbRPtRpX65oyxhq1KjzuI/"
    doc_format = "export?format=csv"

    url = base_url + doc_id + doc_format

    df_raw = pd.read_csv(url)
    return (df_raw,)


@app.cell
def _():
    return


@app.cell
def _(df_raw, pd):
    ### Written entirely by AI
    # only the years 2000 to 2020, plus the three columns the README asks us to create
    data = df_raw.copy()
    data["year"] = pd.to_datetime(data["date"]).dt.year
    data = data[(data["year"] >= 2000) & (data["year"] <= 2020)].copy()
    data["gdp_per_capita"] = data["GDP_current_US"] / data["population"]
    data["co2_per_capita"] = data["CO2_emisions"] * 1000 / data["population"]
    data["rural_population%"] = data["rural_population"] / data["population"] * 100
    return (data,)


@app.cell
def _():
    ### Written entirely by AI
    # our choices: main indicator, comparison indicators (with the direction the claim expects),
    # start countries, colours, and the rows that are not countries
    main_col = "co2_per_capita"
    main_label = "CO2 emissions per person (tonnes)"

    # expect = +1: the claim expects a positive correlation with CO2 per person, -1: a negative one
    indicators = {
        "GDP per capita (US$)": {
            "col": "gdp_per_capita", "expect": 1,
            "text": "richer countries emit more CO2 per person",
        },
        "Internet users (% of population)": {
            "col": "individuals_using_internet%", "expect": 1,
            "text": "more developed countries (more internet use) emit more CO2 per person",
        },
        "Rural population (% of total)": {
            "col": "rural_population%", "expect": -1,
            "text": "less developed, more rural countries emit less CO2 per person",
        },
        "Renewable energy (% of final energy use)": {
            "col": "renewvable_energy_consumption%", "expect": -1,
            "text": "countries with more renewable energy emit less CO2 per person",
        },
    }

    default_countries = [
        "United States", "Germany", "United Kingdom",
        "China", "India", "Viet Nam", "Brazil", "Nigeria",
    ]
    palette = [
        "#2563eb", "#dc2626", "#059669", "#d97706", "#7c3aed", "#0891b2",
        "#db2777", "#65a30d", "#475569", "#ea580c", "#0d9488", "#9333ea",
    ]

    aggregates = [
        "Africa Eastern and Southern", "Africa Western and Central", "Arab World",
        "Caribbean small states", "Central Europe and the Baltics",
        "Early-demographic dividend", "East Asia & Pacific",
        "East Asia & Pacific (IDA & IBRD countries)", "East Asia & Pacific (IDA & IBRD)",
        "East Asia & Pacific (excluding high income)", "Euro area", "Europe & Central Asia",
        "Europe & Central Asia (IDA & IBRD countries)", "Europe & Central Asia (IDA & IBRD)",
        "Europe & Central Asia (excluding high income)", "European Union",
        "Fragile and conflict affected situations", "Heavily indebted poor countries (HIPC)",
        "High income", "IBRD only", "IDA & IBRD total", "IDA blend", "IDA only", "IDA total",
        "Late-demographic dividend", "Latin America & Caribbean",
        "Latin America & Caribbean (IDA & IBRD)", "Latin America & Caribbean (excluding high income)",
        "Latin America & the Caribbean (IDA & IBRD countries)",
        "Least developed countries: UN classification", "Low & middle income", "Low income",
        "Lower middle income", "Middle East & North Africa",
        "Middle East & North Africa (IDA & IBRD countries)", "Middle East & North Africa (IDA & IBRD)",
        "Middle East & North Africa (excluding high income)", "Middle income", "North America",
        "Not classified", "OECD members", "Other small states", "Pacific island small states",
        "Post-demographic dividend", "Pre-demographic dividend", "Small states", "South Asia",
        "South Asia (IDA & IBRD)", "Sub-Saharan Africa", "Sub-Saharan Africa (IDA & IBRD countries)",
        "Sub-Saharan Africa (IDA & IBRD)", "Sub-Saharan Africa (excluding high income)",
        "Upper middle income", "World",
    ]
    old_names = ["Czech Republic", "Turkey", "Vietnam"]
    return (
        aggregates,
        default_countries,
        indicators,
        main_col,
        main_label,
        old_names,
        palette,
    )


@app.cell
def _(aggregates, data, default_countries, indicators, mo, old_names):
    ### Written entirely by AI
    # the controls: indicator and period (required), countries and year-to-year switch (extras)
    _countries = sorted(set(data["country"]) - set(aggregates) - set(old_names))

    indicator = mo.ui.dropdown(
        options=list(indicators), value=list(indicators)[0], label="Compare with"
    )
    period = mo.ui.range_slider(
        start=2000, stop=2020, step=1, value=[2000, 2020],
        label="Period", show_value=True, full_width=True,
    )
    countries = mo.ui.multiselect(
        options=_countries, value=default_countries, label="Countries", max_selections=12
    )
    changes = mo.ui.switch(value=False, label="Test year-to-year changes")
    return changes, countries, indicator, period


@app.cell
def _(alt, changes, countries, indicator, indicators, palette, period):
    ### Written entirely by AI
    # what the user has chosen, read in one place
    start_year, end_year = period.value
    x_label = indicator.value
    x_info = indicators[x_label]
    selected = list(countries.value)
    changes_on = changes.value
    color_scale = alt.Scale(domain=selected, range=palette[: len(selected)])
    return changes_on, color_scale, end_year, selected, start_year, x_info, x_label


@app.cell
def _(pg):
    ### Written entirely by AI
    # one correlation test for one country (Spearman, with Pearson only as a check)
    def corr_for(frame, x, y, start, end, changes):
        # one row per year of the period, so that gaps in the data stay gaps
        g = frame.drop_duplicates("year").set_index("year")[[x, y]].reindex(range(start, end + 1))
        if changes:
            g = g.diff()          # change from one year to the next
        g = g.dropna()
        n = len(g)
        if n < 5:
            return {"status": "few", "n": n}
        if g[x].nunique() < 2 or g[y].nunique() < 2:
            return {"status": "flat", "n": n}
        spear = pg.corr(g[x], g[y], method="spearman")
        pear = pg.corr(g[x], g[y], method="pearson")
        r = float(spear["r"].iloc[0])
        if r != r:
            return {"status": "flat", "n": n}
        ci = spear["CI95"].iloc[0]
        return {
            "status": "ok", "n": n, "r": r, "p": float(spear["p_val"].iloc[0]),
            "ci_low": float(ci[0]), "ci_high": float(ci[1]),
            "pearson": float(pear["r"].iloc[0]), "data": g.reset_index(),
        }

    return (corr_for,)


@app.cell
def _(changes_on, corr_for, data, end_year, main_col, pd, selected, start_year, x_info):
    ### Written entirely by AI
    # one test per country, for the chosen indicator and period
    _rows = []
    _frames = []
    for _c in selected:
        _res = corr_for(data[data["country"] == _c], x_info["col"], main_col,
                        start_year, end_year, changes_on)
        _row = {"country": _c, "status": _res["status"], "n": _res["n"]}
        if _res["status"] == "ok":
            for _k in ["r", "p", "ci_low", "ci_high", "pearson"]:
                _row[_k] = _res[_k]
            _frame = _res["data"].rename(columns={x_info["col"]: "x", main_col: "y"})
            _frame["country"] = _c
            _frames.append(_frame)
        _rows.append(_row)

    _columns = ["country", "status", "n", "r", "p", "ci_low", "ci_high", "pearson"]
    results = pd.DataFrame(_rows, columns=_columns)
    plot_df = pd.concat(_frames) if _frames else pd.DataFrame(columns=["year", "x", "y", "country"])
    return plot_df, results


@app.cell
def _(alt, changes_on, color_scale, main_label, mo, plot_df, x_label):
    ### Written entirely by AI
    # the main view: one colour, one cloud of points and one trend line per country
    if len(plot_df) == 0:
        scatter_view = mo.callout(
            "No country has enough years with data for this choice. Change the period, the indicator or the countries.",
            kind="warn",
        )
    else:
        _x_title = ("Change in " + x_label) if changes_on else x_label
        _y_title = ("Change in " + main_label) if changes_on else main_label
        _pick = alt.selection_point(fields=["country"], bind="legend")
        _base = alt.Chart(plot_df)
        _points = _base.mark_circle(size=75, stroke="white", strokeWidth=0.8).encode(
            x=alt.X("x:Q", title=_x_title, scale=alt.Scale(zero=False)),
            y=alt.Y("y:Q", title=_y_title, scale=alt.Scale(zero=False)),
            color=alt.Color("country:N", scale=color_scale,
                            legend=alt.Legend(title=None, orient="bottom", columns=4, symbolSize=120)),
            opacity=alt.condition(_pick, alt.value(0.85), alt.value(0.1)),
            tooltip=[
                alt.Tooltip("country:N", title="Country"),
                alt.Tooltip("year:Q", title="Year", format="d"),
                alt.Tooltip("x:Q", title=x_label, format=",.2f"),
                alt.Tooltip("y:Q", title=main_label, format=",.2f"),
            ],
        )
        _lines = _base.transform_regression("x", "y", groupby=["country"]).mark_line(strokeWidth=2.5).encode(
            x="x:Q", y="y:Q",
            color=alt.Color("country:N", scale=color_scale, legend=None),
            opacity=alt.condition(_pick, alt.value(0.95), alt.value(0.08)),
        )
        scatter_view = (_points + _lines).add_params(_pick).properties(width=520, height=330)
    return (scatter_view,)


@app.cell
def _(changes_on, mo, palette, results, selected, x_info):
    ### Written entirely by AI
    # the test table: one row per country, plus a message for countries we cannot test
    _dot = {c: palette[i] for i, c in enumerate(selected)}
    _ok = results[results["status"] == "ok"].sort_values("r", ascending=False)
    _bad = results[results["status"] != "ok"]

    def _strength(r):
        r = abs(r)
        if r < 0.1:
            return "negligible"
        if r < 0.3:
            return "small"
        if r < 0.5:
            return "moderate"
        return "large"

    def _pill(r):
        _rgb = "13,148,136" if r > 0 else "225,29,72"
        _alpha = 0.12 + 0.88 * abs(r)
        _text = "#ffffff" if abs(r) > 0.55 else "inherit"
        return (
            '<span style="display:inline-block;min-width:54px;text-align:center;padding:2px 8px;'
            'border-radius:999px;font-weight:700;background:rgba(' + _rgb + ',' + f"{_alpha:.2f}" + ');color:' + _text + ';">'
            + f"{r:+.2f}" + "</span>"
        )

    def _claim(r):
        if abs(r) < 0.1:
            return '<span style="opacity:.6;">&ndash; no direction</span>'
        if (r > 0) == (x_info["expect"] > 0):
            return '<span style="color:#15803d;font-weight:600;">&#10004; as expected</span>'
        return '<span style="color:#b91c1c;font-weight:600;">&#10008; opposite</span>'

    _th = ('<th style="text-align:left;padding:6px 8px;font-size:11px;letter-spacing:.06em;'
           'text-transform:uppercase;opacity:.6;font-weight:600;">')
    _html = ('<table style="border-collapse:collapse;width:100%;font-size:13px;">'
             '<thead><tr>' + _th + 'Country</th>' + _th + 'Years</th>' + _th + 'r</th>'
             + _th + '95% CI</th>' + _th + 'p</th>' + _th + 'Strength</th>' + _th + 'Claim</th></tr></thead><tbody>')
    for _, _r in _ok.iterrows():
        _p_text = "&lt;0.001" if _r["p"] < 0.001 else f"{_r['p']:.3f}"
        _p_style = "font-weight:700;" if _r["p"] < 0.05 else "opacity:.7;"
        _html += (
            '<tr style="border-top:1px solid rgba(128,128,128,.22);">'
            '<td style="padding:6px 8px;white-space:nowrap;"><span style="display:inline-block;width:10px;height:10px;'
            'border-radius:50%;margin-right:7px;background:' + _dot[_r["country"]] + ';"></span>' + _r["country"] + '</td>'
            '<td style="padding:6px 8px;">' + str(int(_r["n"])) + '</td>'
            '<td style="padding:6px 8px;">' + _pill(_r["r"]) + '</td>'
            '<td style="padding:6px 8px;white-space:nowrap;opacity:.8;">[' + f"{_r['ci_low']:.2f}, {_r['ci_high']:.2f}" + ']</td>'
            '<td style="padding:6px 8px;' + _p_style + '">' + _p_text + '</td>'
            '<td style="padding:6px 8px;">' + _strength(_r["r"]) + '</td>'
            '<td style="padding:6px 8px;white-space:nowrap;">' + _claim(_r["r"]) + '</td></tr>'
        )
    _html += "</tbody></table>"

    _what = "year-to-year changes" if changes_on else "yearly values"
    _agree = int(((_ok["pearson"] > 0) == (_ok["r"] > 0)).sum()) if len(_ok) else 0
    _head = (
        '<div style="font-size:13px;line-height:1.5;margin-bottom:6px;">'
        '<b>Spearman rank correlation</b> on the ' + _what + ' of each country. We chose Spearman because '
        'the points often follow a curve and a few extreme years (the 2009 and 2020 dips) would pull a Pearson line. '
        'As a check, Pearson points the same way in ' + str(_agree) + ' of ' + str(len(_ok)) + ' countries.</div>'
    )
    _foot = (
        '<div style="font-size:11.5px;opacity:.65;margin-top:6px;">H0: no monotonic relationship in that country. '
        'Bold p = significant at 5%. p-values are too optimistic because neighbouring years are not independent.</div>'
    )

    _parts = [mo.Html(_head), mo.Html(_html), mo.Html(_foot)]
    if len(_bad):
        _notes = []
        for _, _r in _bad.iterrows():
            if _r["status"] == "few":
                _notes.append(f"**{_r['country']}**: only {int(_r['n'])} years with data (at least 5 needed)")
            else:
                _notes.append(f"**{_r['country']}**: one of the two indicators does not change in this period")
        _parts.append(mo.callout(mo.md("Not tested: " + "; ".join(_notes) + "."), kind="warn"))
    if len(_ok) == 0:
        _parts = [mo.callout("No country can be tested with this choice.", kind="warn")] + _parts[3:]
    table_view = mo.vstack(_parts, gap=0.5)
    return (table_view,)


@app.cell
def _(changes_on, mo, results, x_info):
    ### Written entirely by AI
    # the verdict, in plain words, computed from the table
    _ok = results[results["status"] == "ok"]
    _n = len(_ok)
    if _n == 0:
        verdict_view = mo.callout("No verdict possible: no country has enough data for this choice.", kind="warn")
    else:
        _sign = 1 if x_info["expect"] > 0 else -1
        _clear = _ok[_ok["r"].abs() >= 0.1]
        _expected = _clear[(_clear["r"] > 0) == (_sign > 0)]
        _opposite = _clear[(_clear["r"] > 0) != (_sign > 0)]
        _none = _n - len(_clear)
        _strong = int((_ok["r"].abs() > 0.5).sum())
        _signif = int((_ok["p"] < 0.05).sum())
        _sig_exp = int((_expected["p"] < 0.05).sum())
        _sig_opp = int((_opposite["p"] < 0.05).sum())

        if _n < 3:
            _label, _color, _sentence = "Cannot tell", "#475569", "Fewer than three countries can be tested, so there is nothing to generalise."
        elif _sig_exp >= 0.7 * _n and _sig_opp == 0:
            _label, _color, _sentence = "Supports the claim", "#15803d", "For these countries and this period the data supports the claim."
        elif _sig_opp >= 0.7 * _n and _sig_exp == 0:
            _label, _color, _sentence = "Contradicts the claim", "#b91c1c", "For these countries and this period the data contradicts the claim."
        elif _sig_exp + _sig_opp == 0:
            _label, _color, _sentence = "Cannot tell", "#475569", "No country shows a statistically significant correlation, so the data cannot tell."
        else:
            _label, _color, _sentence = "Mixed picture", "#b45309", "For these countries and this period the data gives a mixed picture: the claim holds in some countries and fails in others."

        _text = (
            _sentence + f" In {len(_expected)} of {_n} countries the correlation points the way the claim expects "
            f"({x_info['text']}) and in {len(_opposite)} it points the opposite way"
        )
        if len(_opposite):
            _text += " (" + ", ".join(_opposite.sort_values("r")["country"]) + ")"
        if _none:
            _text += f", and {_none} show no direction"
        _text += f". {_strong} of {_n} correlations are strong (above 0.5) and {_signif} are significant at 5%."
        if changes_on:
            _care = ("These are year-to-year changes, so shared time trends are removed, but a correlation "
                     "still cannot show that one indicator causes the other.")
        else:
            _care = ("A correlation cannot show cause, and two indicators that both drift over time correlate "
                     "even if they are unrelated: see the tab \"Trend or real link?\".")
        verdict_view = mo.Html(
            '<div style="border-left:6px solid ' + _color + ';padding:10px 16px;border-radius:6px;'
            'background:rgba(128,128,128,.08);font-size:14px;line-height:1.55;">'
            '<div style="font-size:12px;letter-spacing:.1em;text-transform:uppercase;font-weight:700;color:' + _color + ';">'
            'Verdict &middot; ' + _label + '</div>' + _text + ' ' + _care + '</div>'
        )
    return (verdict_view,)


@app.cell
def _(
    alt,
    color_scale,
    data,
    end_year,
    main_col,
    main_label,
    mo,
    selected,
    start_year,
    x_info,
    x_label,
):
    ### Written entirely by AI
    # over time: the trends behind the correlation, one line per country
    _years = data[
        data["country"].isin(selected) & (data["year"] >= start_year) & (data["year"] <= end_year)
    ]
    if len(selected) == 0 or _years[[main_col, x_info["col"]]].dropna(how="all").empty:
        time_view = mo.callout("No data to show for this choice.", kind="warn")
    else:
        _charts = []
        for _col, _title, _legend in [(main_col, main_label, None), (x_info["col"], x_label, alt.Legend(title=None))]:
            _sub = _years[["country", "year", _col]].dropna()
            _charts.append(
                alt.Chart(_sub).mark_line(point=alt.OverlayMarkDef(size=28), strokeWidth=2.2).encode(
                    x=alt.X("year:Q", title=None, axis=alt.Axis(format="d", tickMinStep=2),
                            scale=alt.Scale(zero=False)),
                    y=alt.Y(f"{_col}:Q", title=_title, scale=alt.Scale(zero=False)),
                    color=alt.Color("country:N", scale=color_scale, legend=_legend),
                    tooltip=[
                        alt.Tooltip("country:N", title="Country"),
                        alt.Tooltip("year:Q", title="Year", format="d"),
                        alt.Tooltip(f"{_col}:Q", title=_title, format=",.2f"),
                    ],
                ).properties(width=330, height=250)
            )
        time_view = mo.vstack([
            mo.md("Both indicators over the chosen period. If both lines drift in one direction, "
                  "a strong correlation may only come from that shared trend."),
            alt.hconcat(*_charts),
        ])
    return (time_view,)


@app.cell
def _(
    alt,
    corr_for,
    data,
    end_year,
    main_col,
    mo,
    np,
    pd,
    selected,
    start_year,
    x_info,
    x_label,
):
    ### Written entirely by AI
    # trend or real link? the same test on the yearly values and on the year-to-year changes
    _rows = []
    for _c in selected:
        _frame = data[data["country"] == _c]
        _lv = corr_for(_frame, x_info["col"], main_col, start_year, end_year, False)
        _ch = corr_for(_frame, x_info["col"], main_col, start_year, end_year, True)
        if _lv["status"] == "ok" and _ch["status"] == "ok":
            _rows.append({"country": _c, "levels": _lv["r"], "changes": _ch["r"],
                          "p_changes": _ch["p"], "n_changes": _ch["n"]})
    _both = pd.DataFrame(_rows, columns=["country", "levels", "changes", "p_changes", "n_changes"])

    if len(_both) < 2:
        trend_view = mo.callout(
            "Not enough countries with data for both tests. Widen the period or choose other countries.",
            kind="warn",
        )
    else:
        _order = list(_both.sort_values("levels", ascending=False)["country"])
        _long = _both.melt(id_vars="country", value_vars=["levels", "changes"], var_name="kind", value_name="r")
        _long["kind"] = _long["kind"].map({"levels": "yearly values", "changes": "year-to-year changes"})
        _y = alt.Y("country:N", sort=_order, title=None)
        _rule = alt.Chart(_both).mark_rule(strokeWidth=3, color="#cbd5e1").encode(
            y=_y, x=alt.X("levels:Q", scale=alt.Scale(domain=[-1, 1]), title="Spearman r"), x2="changes:Q"
        )
        _dots = alt.Chart(_long).mark_point(filled=True, size=150, opacity=1).encode(
            y=_y, x=alt.X("r:Q", scale=alt.Scale(domain=[-1, 1])),
            color=alt.Color("kind:N", title=None, scale=alt.Scale(
                domain=["yearly values", "year-to-year changes"], range=["#0f172a", "#f97316"])),
            tooltip=[alt.Tooltip("country:N", title="Country"), alt.Tooltip("kind:N", title="Test"),
                     alt.Tooltip("r:Q", title="r", format="+.2f")],
        )
        _zero = alt.Chart(pd.DataFrame({"x": [0]})).mark_rule(color="#64748b", strokeDash=[4, 4]).encode(x="x:Q")
        _chart = (_zero + _rule + _dots).properties(width=520, height=max(120, 34 * len(_both)))

        _big_levels = int((_both["levels"].abs() >= 0.8).sum())
        _big_changes = int((_both["changes"].abs() >= 0.8).sum())
        _m1 = float(np.median(_both["levels"].abs()))
        _m2 = float(np.median(_both["changes"].abs()))
        _sig_changes = int((_both["p_changes"] < 0.05).sum())
        trend_view = mo.vstack([
            mo.md(
                f"**Is it a real link or just two lines that drift in time?** For *{x_label}* and CO2 per person, "
                f"{_big_levels} of {len(_both)} countries have a very strong correlation (|r| of 0.8 or more) in the yearly values. "
                f"Once the shared trend is removed (year-to-year changes) only {_big_changes} do, the typical |r| falls from "
                f"{_m1:.2f} to {_m2:.2f}, and {_sig_changes} stay significant. "
                "Where the two dots are far apart, the strong correlation mostly came from time, not from the indicators moving together."
            ),
            _chart,
        ])
    return (trend_view,)


@app.cell
def _(alt, changes_on, main_label, mo, plot_df, x_label, color_scale):
    ### Written entirely by AI
    # distributions: a check for Pearson or Spearman, kept small
    if len(plot_df) == 0:
        dist_view = mo.callout("No data to show for this choice.", kind="warn")
    else:
        _prefix = "Change in " if changes_on else ""
        _charts = []
        _skews = []
        for _col, _title in [("y", _prefix + main_label), ("x", _prefix + x_label)]:
            _skews.append(float(plot_df[_col].skew()))
            _charts.append(
                alt.Chart(plot_df).mark_bar().encode(
                    x=alt.X(f"{_col}:Q", bin=alt.Bin(maxbins=20), title=_title),
                    y=alt.Y("count()", title="country-years"),
                    color=alt.Color("country:N", scale=color_scale, legend=None),
                    tooltip=[alt.Tooltip("country:N", title="Country"), alt.Tooltip("count()", title="country-years")],
                ).properties(width=330, height=230)
            )
        _skewed = abs(_skews[0]) > 1 or abs(_skews[1]) > 1
        dist_view = mo.vstack([
            mo.md(
                f"Skewness: {_skews[0]:.2f} for CO2 per person and {_skews[1]:.2f} for the chosen indicator. "
                + ("At least one is clearly skewed, which supports using Spearman."
                   if _skewed else
                   "Both are fairly symmetric, but the points of single countries still often follow curves, so Spearman stays the safer choice.")
                + " Colours are the countries."
            ),
            alt.hconcat(*_charts),
        ])
    return (dist_view,)


@app.cell
def _(
    changes,
    countries,
    dist_view,
    indicator,
    mo,
    period,
    scatter_view,
    selected,
    table_view,
    time_view,
    trend_view,
    verdict_view,
):
    ### Written entirely by AI
    # the page: title, members, our choices, controls, then the main view and the tabs
    def _card(title, text):
        return mo.Html(
            '<div style="flex:1;min-width:230px;padding:12px 16px;border-radius:12px;'
            'background:rgba(128,128,128,.08);border:1px solid rgba(128,128,128,.18);'
            'font-size:12.5px;line-height:1.5;"><div style="font-size:11px;letter-spacing:.1em;'
            'text-transform:uppercase;font-weight:700;color:#0f766e;margin-bottom:3px;">' + title + '</div>' + text + '</div>'
        )

    _header = mo.Html(
        '<div style="background:linear-gradient(115deg,#0b1f2a 0%,#0f4c4a 55%,#16a34a 130%);color:#fff;'
        'padding:22px 28px;border-radius:16px;">'
        '<div style="font-size:12px;letter-spacing:.16em;text-transform:uppercase;opacity:.7;">'
        'Group 1 &middot; Checking popular claims with World Bank data</div>'
        '<div style="font-size:27px;font-weight:700;line-height:1.25;margin:6px 0 6px 0;">'
        'Group 1 &middot; &ldquo;As countries get richer, they pollute more.&rdquo;</div>'
        '<div style="font-size:14px;opacity:.9;">Members: Muhammad Abdullah Yousaf, Saddam Khan'
        '<span style="opacity:.6;"> &nbsp;|&nbsp; ' + str(len(selected)) + ' countries &middot; 2000&ndash;2020</span></div></div>'
    )

    _choices = mo.hstack([
        _card("Why this claim",
              "It is repeated in almost every climate debate, to argue for and against growth. "
              "The data can show if it is a law of nature or only a stage of development."),
        _card("Why these indicators",
              "CO2 per person is fair to big and small countries. We compare it with GDP per capita (the claim itself), "
              "two other signs of development (internet use, share of rural population) and the renewable energy share."),
        _card("Why these countries",
              "Rich (USA, Germany, UK), fast-growing (China, India, Viet Nam), middle income (Brazil) and low income (Nigeria): "
              "five regions, all with a full 2000&ndash;2020 record."),
    ], gap=0.75, wrap=True, justify="space-between")

    _controls = mo.vstack([
        mo.hstack([indicator, period], justify="start", gap=2, align="center", widths=[1, 2]),
        mo.hstack([countries, changes], justify="start", gap=2, align="center", widths=[2, 1]),
    ], gap=0.4).style({
        "padding": "10px 16px", "border-radius": "12px",
        "background": "rgba(15,118,110,.07)", "border": "1px solid rgba(15,118,110,.25)",
    })

    _claim_tab = mo.vstack([
        mo.hstack([scatter_view, table_view], widths=[1.05, 1], gap=1, align="start"),
        verdict_view,
    ], gap=0.9)

    _tabs = mo.ui.tabs({
        "Claim check": _claim_tab,
        "Over time": time_view,
        "Trend or real link?": trend_view,
        "Distributions": dist_view,
    })

    mo.vstack([
        _header,
        _choices,
        mo.md("*How to use: choose an indicator and a period, read the table and the verdict. "
              "Click a country in the legend to highlight it. The switch tests year-to-year changes.*"),
        _controls,
        _tabs,
    ], gap=0.8)
    return


if __name__ == "__main__":
    app.run()
