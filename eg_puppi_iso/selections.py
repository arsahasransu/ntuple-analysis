from python.selections import Selection

# Select for events with prompt gen electrons
gen_prompt_el_sel = [Selection('GenPromptE', 'p_{T}^{TOBJ} #geq 10 GeV', lambda array: array.pt >= 10),]