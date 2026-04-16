def format_baseball_email(slate):
    lines = []
    lines.append("EDGE EQUATION — BASEBALL SLATE\n")

    def block(title, plays):
        if not plays:
            return
        lines.append(title + ":")
        for p in plays:
            lines.append(
                f"• {p['player']} — {p['prop_label']} {p['display_line']} "
                f"(λ={round(p['true_lambda'],2)}, edge={round(p['edge']*100,1)}%)"
            )
        lines.append("")

    block("NRFI/YRFI", slate["nrfi"])
    block("Pitcher Ks", slate["k_props"])
    block("Hits", slate["hits"])
    block("Total Bases", slate["total_bases"])
    block("Home Runs", slate["home_runs"])
    block("RBI", slate["rbi"])
    block("Runs", slate["runs"])

    lines.append("This is data. Not advice.\n#EdgeEquation")
    return "\n".join(lines)
