import marimo

__generated_with = "0.25.2"
app = marimo.App(width="medium")


@app.cell
def _():
    return


@app.cell(hide_code=True)
def _(mo):
    ### Written entirely by AI
    mo.md("""
    # Group 1 · What drives Airbnb prices in Europe?

    **Members:** Saddam Khan, Muhammad Abdullah Yousaf

    Data: 51,707 Airbnb listings in 10 European cities, on weekdays and weekends
    ([Gyódi & Nawaro, 2021](https://zenodo.org/record/4446043)).
    All prices are **per night** (the original price is for two nights). Because a few listings are extremely
    expensive, the tests use the **logarithm of the price**, which makes the distributions much more symmetric.
    """)
    return


@app.cell
def _():
    return


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import altair as alt
    import numpy as np
    import pingouin as pg

    return alt, mo, np, pd, pg


@app.cell
def _(pd):
    base_url = "https://docs.google.com/spreadsheets/d/"
    doc_id = "1ecopK6oyyb4d_7-QLrCr8YlgFrCetHU7-VQfnYej7JY/"
    format_doc = "export/format=excel"

    url = base_url + doc_id + format_doc

    excel_file = pd.ExcelFile(url)
    return (excel_file,)


@app.cell
def _(excel_file, pd):
    dfs = []

    for sheet in excel_file.sheet_names:
        _df = excel_file.parse(sheet)
        _df["city"] = sheet.split("_")[0]
        _df["type_of_day"] = sheet.split("_")[1]
        dfs.append(_df)

    df = pd.concat(dfs, ignore_index=True)
    return (df,)


@app.cell
def _(df, np, pd):
    # clean data: log price, readable labels and the categories we analyse
    print("columns in the data:", list(df.columns))

    data = df[df["realSum"] > 0].dropna(subset=["dist", "person_capacity"]).copy()
    data["price"] = data["realSum"]
    data["log_price"] = np.log(data["price"])

    data["city"] = data["city"].str.capitalize()
    data["distance"] = pd.cut(
        data["dist"], bins=[-1, 1, 2, 4, 1000],
        labels=["0-1 km", "1-2 km", "2-4 km", "over 4 km"],
    ).astype(str)
    data["guests"] = pd.cut(
        data["person_capacity"], bins=[0, 2, 4, 100],
        labels=["1-2 guests", "3-4 guests", "5+ guests"],
    ).astype(str)
    _is_super = data["host_is_superhost"].astype(str).str.lower() == "true"
    data["superhost"] = np.where(_is_super, "superhost", "no superhost")

    # label shown to the user -> column in the data
    factors = {
        "City": "city",
        "Room type": "room_type",
        "Weekday or weekend": "type_of_day",
        "Distance to centre": "distance",
        "Superhost": "superhost",
        "Guests": "guests",
    }
    return data, factors


@app.cell
def _(data, factors, mo):
    # all UI elements: filters (apply to every section) and one choice per section
    _cities = sorted(data["city"].unique())
    _rooms = sorted(data["room_type"].unique())

    cities = mo.ui.multiselect(options=_cities, value=_cities, label="Cities")
    room_types = mo.ui.multiselect(options=_rooms, value=_rooms, label="Room types")
    day = mo.ui.radio(
        options=["all", "weekdays", "weekends"], value="all", label="Days", inline=True
    )

    box_factor = mo.ui.dropdown(options=factors, value="City", label="Show prices by")
    price_axis = mo.ui.radio(
        options={"price in EUR": "euro", "log price": "log"},
        value="price in EUR", label="Axis", inline=True,
    )
    oneway_factor = mo.ui.dropdown(options=factors, value="City", label="Variable")
    factor_a = mo.ui.dropdown(options=factors, value="City", label="Factor A")
    factor_b = mo.ui.dropdown(options=factors, value="Room type", label="Factor B")
    return (
        box_factor,
        cities,
        day,
        factor_a,
        factor_b,
        oneway_factor,
        price_axis,
        room_types,
    )


@app.cell
def _(cities, data, day, room_types):
    # the listings that match the filters
    view = data[data["city"].isin(cities.value) & data["room_type"].isin(room_types.value)]
    if day.value != "all":
        view = view[view["type_of_day"] == day.value]
    return (view,)


@app.cell
def _(pg):
    # helper functions for the ANOVA sections
    def p_column(table):
        # older pingouin versions call it "p-unc", newer ones "p_unc"
        if "p_unc" in table.columns:
            return "p_unc"
        return "p-unc"

    def format_p(p):
        if p < 0.001:
            return "p < 0.001"
        return f"p = {p:.3f}"

    def size_word(np2):
        # rough guide from the README: 0.01 small, 0.06 medium, 0.14 large
        if np2 >= 0.14:
            return "large"
        if np2 >= 0.06:
            return "medium"
        if np2 >= 0.01:
            return "small"
        return "negligible"

    def run_oneway(frame, column):
        # one-way ANOVA of log_price by `column`, including the assumption checks
        sizes = frame.groupby(column)["log_price"].size()
        keep = sizes[sizes >= 5].index          # groups with fewer than 5 listings are ignored
        frame = frame[frame[column].isin(keep)]
        sizes = sizes[keep]
        if len(keep) < 2:
            return None

        table = pg.anova(data=frame, dv="log_price", between=column, detailed=True)
        np2 = table["np2"].iloc[0]

        # assumptions: equal variances (Levene) and normality inside each group
        equal_var_p = pg.homoscedasticity(frame, dv="log_price", group=column)["pval"].iloc[0]
        if sizes.min() >= 8:
            normal = pg.normality(frame, dv="log_price", group=column, method="normaltest")
        else:
            normal = pg.normality(frame, dv="log_price", group=column)
        normal_share = normal["normal"].mean()

        if sizes.min() < 30 and normal_share < 1:
            test = "Kruskal-Wallis test"
            used = pg.kruskal(frame, dv="log_price", between=column)
            why = ("Some groups have fewer than 30 listings and are not bell-shaped, "
                   "so I used the Kruskal-Wallis test, which does not need a bell shape.")
        elif equal_var_p < 0.05:
            test = "Welch ANOVA"
            used = pg.welch_anova(frame, dv="log_price", between=column)
            why = (f"The groups have unequal variances (Levene test, {format_p(equal_var_p)}), "
                   "so I used the Welch ANOVA, which allows for that.")
        else:
            test = "classic one-way ANOVA"
            used = table
            why = (f"The variances are similar (Levene test, {format_p(equal_var_p)}), "
                   "so the classic one-way ANOVA is fine.")

        return {
            "test": test, "why": why, "used": used, "table": table,
            "p": used[p_column(used)].iloc[0], "np2": np2, "sizes": sizes,
            "equal_var_p": equal_var_p, "normal_share": normal_share,
        }

    return format_p, p_column, run_oneway, size_word


@app.cell
def _(alt, factors, mo, pd, run_oneway, size_word, view):
    ### Written entirely by AI
    # which variable matters most? one-way ANOVA for every variable, compared with np2
    _empty = mo.callout(
        "No listings match this selection. Please choose more cities, room types or days.",
        kind="warn",
    )
    if len(view) == 0:
        ranking_view = _empty
        headline = _empty
    else:
        _rows = []
        for _label, _col in factors.items():
            _r = run_oneway(view, _col)
            if _r is not None:
                _rows.append({"variable": _label, "np2": _r["np2"], "p": _r["p"]})

        if len(_rows) < 2:
            ranking_view = mo.callout(
                "Too few groups are left to compare the variables. Please widen the filters.",
                kind="warn",
            )
            headline = ranking_view
        else:
            _rank = pd.DataFrame(_rows).sort_values("np2", ascending=False).reset_index(drop=True)
            _rank["top"] = _rank.index == 0

            _bars = alt.Chart(_rank).mark_bar(cornerRadiusEnd=4, size=26).encode(
                y=alt.Y("variable:N", sort=list(_rank["variable"]), title=None),
                x=alt.X("np2:Q", title="share of the price variation explained (np2)"),
                color=alt.Color(
                    "top:N", legend=None,
                    scale=alt.Scale(domain=[True, False], range=["#0f766e", "#94a3b8"]),
                ),
                tooltip=["variable", alt.Tooltip("np2:Q", format=".3f"), alt.Tooltip("p:Q", format=".3g")],
            )
            _text = _bars.mark_text(align="left", dx=5, fontSize=13).encode(
                text=alt.Text("np2:Q", format=".3f"), color=alt.value("#1f2937")
            )
            _lines = alt.Chart(pd.DataFrame({"x": [0.01, 0.06, 0.14]})).mark_rule(
                strokeDash=[4, 4], color="#cbd5e1"
            ).encode(x="x:Q")
            _chart = (_lines + _bars + _text).properties(width="container", height=240)

            _first = _rank.iloc[0]
            _second = _rank.iloc[1]
            _last = _rank.iloc[-1]
            _text_md = (
                f"**{_first['variable']}** matters most: it explains about {_first['np2']:.0%} of the "
                f"variation in (log) price (np2 = {_first['np2']:.2f}, a {size_word(_first['np2'])} effect). "
                f"Second is **{_second['variable']}** (np2 = {_second['np2']:.2f}, {size_word(_second['np2'])}). "
                f"**{_last['variable']}** matters least (np2 = {_last['np2']:.3f}, {size_word(_last['np2'])})."
            )
            ranking_view = mo.vstack([
                mo.md("Each bar comes from one one-way ANOVA. The dashed lines mark np2 = 0.01 (small), "
                      "0.06 (medium) and 0.14 (large)."),
                _chart,
                mo.md(_text_md),
            ])
            headline = mo.callout(mo.md("**Short answer for Henrik.** " + _text_md), kind="success")
    return headline, ranking_view


@app.cell
def _(alt, box_factor, factors, mo, pd, price_axis, view):
    # boxplots of the price by the chosen variable
    # the box values are computed here and only they are sent to the chart (51,707 rows are too big)
    if len(view) == 0:
        boxplot_view = mo.callout(
            "No listings match this selection. Please choose more cities, room types or days.",
            kind="warn",
        )
    else:
        _col = box_factor.value
        _label = [k for k, v in factors.items() if v == _col][0]
        _y = "price" if price_axis.value == "euro" else "log_price"
        if price_axis.value == "euro":
            _scale = alt.Scale(type="log")
            _title = "price per night (EUR, log scale)"
        else:
            _scale = alt.Scale(zero=False)
            _title = "log price"

        _boxes = []
        _dots = []
        for _name, _values in view.groupby(_col)[_y]:
            _q1, _median, _q3 = _values.quantile([0.25, 0.5, 0.75])
            _iqr = _q3 - _q1
            _inside = _values[(_values >= _q1 - 1.5 * _iqr) & (_values <= _q3 + 1.5 * _iqr)]
            _boxes.append({"group": _name, "q1": _q1, "median": _median, "q3": _q3,
                           "low": _inside.min(), "high": _inside.max(), "listings": len(_values)})
            _outliers = _values[~_values.index.isin(_inside.index)]
            if len(_outliers) > 300:
                _outliers = _outliers.sample(300, random_state=1)
            for _v in _outliers:
                _dots.append({"group": _name, "value": _v})

        _boxes = pd.DataFrame(_boxes)
        _dots = pd.DataFrame(_dots, columns=["group", "value"])
        _order = list(_boxes.sort_values("median", ascending=False)["group"])

        _x = alt.X("group:N", sort=_order, title=_label, axis=alt.Axis(labelAngle=-30))
        _whisker = alt.Chart(_boxes).mark_rule(color="#0f766e").encode(
            x=_x, y=alt.Y("low:Q", scale=_scale, title=_title,
                          axis=alt.Axis(format=",.0f", gridOpacity=0.35)), y2="high:Q",
        )
        _box = alt.Chart(_boxes).mark_bar(size=30, color="#14b8a6").encode(
            x=_x, y=alt.Y("q1:Q", scale=_scale), y2="q3:Q",
            tooltip=["group", alt.Tooltip("median:Q", format=".2f"), "listings"],
        )
        _line = alt.Chart(_boxes).mark_tick(color="#0f172a", size=30, thickness=2).encode(
            x=_x, y=alt.Y("median:Q", scale=_scale),
        )
        _points = alt.Chart(_dots).mark_circle(size=25, opacity=0.35, color="#0f766e").encode(
            x=_x, y=alt.Y("value:Q", scale=_scale),
        )
        _chart = (_whisker + _box + _line + _points).properties(width="container", height=380)

        boxplot_view = mo.vstack([
            mo.md(f"**Price per night by {_label.lower()}.** The box holds the middle 50% of the listings, "
                  "the dark line is the median, the dots are unusually expensive or cheap listings. "
                  "Groups are sorted from the highest to the lowest median."),
            _chart,
        ])
    return (boxplot_view,)


@app.cell
def _(alt, factors, format_p, mo, oneway_factor, run_oneway, size_word, view):
    # one-way ANOVA for the chosen variable: hypothesis, assumptions, result, interpretation
    _col = oneway_factor.value
    _label = [k for k, v in factors.items() if v == _col][0]
    _result = run_oneway(view, _col) if len(view) > 0 else None

    if _result is None:
        oneway_view = mo.callout(
            f"Fewer than two {_label.lower()} groups are left with this selection, so there is "
            "nothing to compare. Please change the filters or choose another variable.",
            kind="warn",
        )
    else:
        _median = view.groupby(_col)["price"].median().sort_values(ascending=False)
        _median = _median[_result["sizes"].index.intersection(_median.index)]
        _np2 = _result["np2"]
        if _result["p"] < 0.05:
            _verdict = "The differences between the groups are statistically significant, so they are not just chance."
        else:
            _verdict = "The differences between the groups are not statistically significant, so they could be chance."

        _bars = alt.Chart(_median.rename("median price").reset_index()).mark_bar(
            cornerRadiusEnd=4, color="#14b8a6"
        ).encode(
            y=alt.Y(f"{_col}:N", sort="-x", title=None),
            x=alt.X("median price:Q", title="median price per night (EUR)"),
            tooltip=[_col, alt.Tooltip("median price:Q", format=".0f")],
        ).properties(width="container", height=max(120, 30 * len(_median)))

        _sizes = _result["sizes"]
        oneway_view = mo.vstack([
            mo.md(f"**Null hypothesis (H0):** the mean log price is the same in all {_label.lower()} groups."),
            mo.md(
                f"**Assumptions.** Each listing is one observation. The groups have between "
                f"{_sizes.min():,} and {_sizes.max():,} listings"
                f"{' (very different sizes, which makes the test more sensitive to unequal variances)' if _sizes.max() > 10 * _sizes.min() else ''}. "
                f"{_result['why']}"
            ),
            mo.md(
                f"**Result ({_result['test']}):** {format_p(_result['p'])}, np2 = {_np2:.3f}."
            ),
            _bars,
            mo.callout(mo.md(
                f"**In plain words:** {_label} explains about {_np2:.0%} of the variation in price "
                f"({size_word(_np2)} effect). {_verdict} "
                f"**{_median.index[0]}** is the most expensive group (median {_median.iloc[0]:.0f} EUR) and "
                f"**{_median.index[-1]}** the cheapest (median {_median.iloc[-1]:.0f} EUR)."
            ), kind="info"),
            mo.accordion({
                "Show the full ANOVA table (with sums of squares)": mo.ui.table(
                    _result["table"].round(4), selection=None, show_download=False
                ),
            }),
        ])
    return (oneway_view,)


@app.cell
def _(
    alt,
    factor_a,
    factor_b,
    factors,
    format_p,
    mo,
    np,
    p_column,
    pd,
    pg,
    size_word,
    view,
):
    # two-way ANOVA: two variables and their interaction
    _a = factor_a.value
    _b = factor_b.value
    _la = [k for k, v in factors.items() if v == _a][0]
    _lb = [k for k, v in factors.items() if v == _b][0]

    _frame = view
    _dropped = []
    _ok = len(view) > 0 and _a != _b

    if _ok:
        # pingouin needs listings in every combination: drop levels with fewer than 5 in some combination
        while True:
            _counts = pd.crosstab(_frame[_a], _frame[_b])
            if _counts.shape[0] < 2 or _counts.shape[1] < 2:
                break
            _bad_rows = (_counts < 5).sum(axis=1)
            _bad_cols = (_counts < 5).sum(axis=0)
            if _bad_rows.max() == 0 and _bad_cols.max() == 0:
                break
            if _bad_rows.max() >= _bad_cols.max():
                _level, _which = _bad_rows.idxmax(), _a
            else:
                _level, _which = _bad_cols.idxmax(), _b
            _frame = _frame[_frame[_which] != _level]
            _dropped.append(str(_level))
        _counts = pd.crosstab(_frame[_a], _frame[_b])
        _ok = _counts.shape[0] >= 2 and _counts.shape[1] >= 2

    if len(view) == 0:
        twoway_view = mo.callout("No listings match this selection. Please widen the filters.", kind="warn")
    elif _a == _b:
        twoway_view = mo.callout("Factor A and factor B are the same. Please choose two different variables.", kind="warn")
    elif not _ok:
        twoway_view = mo.callout(
            f"With this selection {_la} and {_lb} do not have at least two groups each with enough "
            "listings. Please change the filters or choose other variables.",
            kind="warn",
        )
    else:
        _table = pg.anova(data=_frame, dv="log_price", between=[_a, _b], detailed=True)
        _p = p_column(_table)
        _names = [_la, _lb, f"{_la} x {_lb}", "Residual"]
        _np2 = _table["np2"].tolist()
        _pv = _table[_p].tolist()

        _show = _table[["SS", "DF", "F", "np2"]].round(3)
        _show.insert(0, "Source", _names)
        _show["p"] = ["<0.001" if v < 0.001 else f"{v:.3f}" for v in _pv[:3]] + [""]

        # equal variances over all combinations
        _cell = (_frame[_a].astype(str) + " | " + _frame[_b].astype(str)).rename("combination")
        _levene = pg.homoscedasticity(
            _frame.assign(combination=_cell), dv="log_price", group="combination"
        )["pval"].iloc[0]
        _min_cell = int(_counts.min().min())
        _max_cell = int(_counts.max().max())

        def _sentence(name, np2, p):
            if p < 0.05:
                return f"**{name}**: effect is {size_word(np2)} (np2 = {np2:.3f}, {format_p(p)})."
            return f"**{name}**: no clear effect (np2 = {np2:.3f}, {format_p(p)})."

        _group = _frame.groupby(_a)["price"].median().sort_values(ascending=False)
        _inter = _np2[2]
        if _pv[2] < 0.05 and _inter >= 0.01:
            _inter_text = (
                f"The effect of {_la.lower()} depends on {_lb.lower()}: the lines in the chart are not parallel. "
                f"The interaction is {size_word(_inter)} (np2 = {_inter:.3f})."
            )
        elif _pv[2] < 0.05:
            _inter_text = (
                "The interaction is statistically significant, but it is tiny "
                f"(np2 = {_inter:.3f}), so the lines in the chart are almost parallel."
            )
        else:
            _inter_text = "There is no clear interaction: the lines in the chart are about parallel."

        _means = _frame.groupby([_a, _b])["log_price"].mean().reset_index()
        _means["typical price"] = np.exp(_means["log_price"])
        _base = alt.Chart(_means).encode(
            x=alt.X(f"{_a}:N", title=_la, axis=alt.Axis(labelAngle=-30),
                    sort=alt.EncodingSortField(field="typical price", op="mean", order="descending")),
            y=alt.Y("typical price:Q", title="typical price per night (EUR)", scale=alt.Scale(zero=False)),
            color=alt.Color(f"{_b}:N", title=_lb, scale=alt.Scale(scheme="tableau10")),
            tooltip=[_a, _b, alt.Tooltip("typical price:Q", format=".0f")],
        )
        _chart = (_base.mark_line(strokeWidth=2.5) + _base.mark_point(size=70, filled=True)).properties(
            width="container", height=340
        )

        _notes = []
        if _dropped:
            _notes.append("Left out because some combinations had fewer than 5 listings: " + ", ".join(_dropped) + ".")
        _notes.append(f"The combinations have between {_min_cell:,} and {_max_cell:,} listings.")
        if _levene < 0.05:
            _notes.append(
                f"The variances differ between combinations (Levene test, {format_p(_levene)}). "
                "pingouin has no Welch version for a two-way ANOVA, so I kept the two-way ANOVA and read it "
                "with care: with this many listings the F-test is fairly robust."
            )
        else:
            _notes.append(f"The variances are similar (Levene test, {format_p(_levene)}), so the ANOVA assumption holds.")

        twoway_view = mo.vstack([
            mo.md(
                "**Null hypotheses (H0), one per row of the table:** "
                f"(1) {_la.lower()} has no effect on the mean log price; "
                f"(2) {_lb.lower()} has no effect on the mean log price; "
                f"(3) no interaction, the effect of {_la.lower()} does not depend on {_lb.lower()}."
            ),
            mo.md("**Assumptions.** Each listing is one observation. " + " ".join(_notes)),
            mo.ui.table(_show, selection=None, show_download=False),
            _chart,
            mo.callout(mo.md(
                "**In plain words:**\n\n"
                f"- {_sentence(_la, _np2[0], _pv[0])} Most expensive: **{_group.index[0]}**, cheapest: **{_group.index[-1]}**.\n"
                f"- {_sentence(_lb, _np2[1], _pv[1])}\n"
                f"- {_inter_text}"
            ), kind="info"),
        ])
    return (twoway_view,)


@app.cell
def _(mo, view):
    # the numbers at the top of the page
    if len(view) == 0:
        stats = mo.md("")
    else:
        stats = mo.hstack([
            mo.stat(f"{len(view):,}", label="listings", bordered=True),
            mo.stat(f"{view['price'].median():.0f} EUR", label="median price per night", bordered=True),
            mo.stat(f"{view['city'].nunique()}", label="cities", bordered=True),
            mo.stat(f"{(view['room_type'] == 'Entire home/apt').mean():.0%}", label="entire homes", bordered=True),
        ], justify="space-around")
    return (stats,)


@app.cell
def _(
    box_factor,
    boxplot_view,
    cities,
    day,
    factor_a,
    factor_b,
    headline,
    mo,
    oneway_factor,
    oneway_view,
    price_axis,
    ranking_view,
    room_types,
    stats,
    twoway_view,
):
    # the page: title and members, filters, then four sections as tabs
    _header = mo.Html("""
    <div style="background:linear-gradient(120deg,#0f172a 0%,#0f766e 100%);color:white;
                padding:28px 32px;border-radius:16px;">
      <div style="font-size:13px;letter-spacing:.14em;text-transform:uppercase;opacity:.75;">
        Group 1 &middot; Applied Statistics and Data Analysis</div>
      <div style="font-size:32px;font-weight:700;margin:6px 0 4px 0;">
        Group 1 &middot; What drives Airbnb prices in Europe?</div>
      <div style="font-size:15px;opacity:.9;">
        Members: Saddam Khan, Muhammad Abdullah Yousaf</div>
      <div style="font-size:13px;opacity:.7;margin-top:6px;">
        Data: Gy&oacute;di &amp; Nawaro (2021), Airbnb listings in ten European cities, weekdays and weekends</div>
    </div>
    """)

    _filters = mo.vstack([
        mo.md("**Filters** &nbsp;(they apply to every section)"),
        mo.hstack([cities, room_types, day], justify="start", gap=2, wrap=True, align="end"),
    ])

    _prices = mo.vstack([
        mo.hstack([box_factor, price_axis], justify="start", gap=2, align="end"),
        boxplot_view,
        mo.md("*Prices are very skewed (a few listings cost thousands of euros), so the tests below use "
              "the logarithm of the price.*"),
    ])

    _oneway = mo.vstack([
        mo.md("### Which variable matters most?"),
        ranking_view,
        mo.md("### Look at one variable in detail (one-way ANOVA)"),
        oneway_factor,
        oneway_view,
    ])

    _twoway = mo.vstack([
        mo.md("Two variables at the same time: does each one matter, and does the effect of one "
              "depend on the other (interaction)? For example: is the price gap between room types "
              "the same in every city?"),
        mo.hstack([factor_a, factor_b], justify="start", gap=2),
        twoway_view,
    ])

    _method = mo.md("""
    ### Why these variables
    - **City**: the question is about Europe, and capitals differ a lot in price.
    - **Room type**: an entire home and a shared room are different products.
    - **Weekday or weekend**: Henrik may want to know whether the timing matters.
    - **Distance to the centre**: location is a classic price driver. The distance is cut into four bands
      because ANOVA needs groups.
    - **Superhost** and **number of guests**: a quality signal of the host and the size of the listing.

    We left out coordinates and the attraction and restaurant indices: they are hard to explain to a client
    and overlap with the distance.

    ### How to read the results
    - **Null hypothesis (H0):** the mean log price is the same in all groups. A small p-value (below 0.05)
      means the groups really differ.
    - With thousands of listings almost every test is significant. That is why we also report
      **np2 (partial eta squared)**: the share of the price variation a variable explains.
      Rough guide: 0.01 small, 0.06 medium, 0.14 large.
    - **Assumptions:** listings are independent; we check equal variances (Levene test) and the bell shape
      inside each group. If the variances differ we use the **Welch ANOVA**; if small groups are not
      bell-shaped we use the **Kruskal-Wallis test**. The section says which test was used and why.
    - Weekday and weekend listings cannot be matched (no listing ID), so they are treated as independent groups.
    """)

    _tabs = mo.ui.tabs({
        "1  Prices": _prices,
        "2  What matters most": _oneway,
        "3  Interactions": _twoway,
        "4  Method": _method,
    })

    mo.vstack([_header, headline, stats, _filters, _tabs], gap=1.25)
    return


if __name__ == "__main__":
    app.run()
