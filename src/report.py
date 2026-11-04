import json,html
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def camel(value):
    if isinstance(value, list):
        return [camel(v) for v in value]
    if isinstance(value, dict):
        def key(k):
            first, *rest = k.split('_')
            return first + ''.join(part.title() for part in rest)
        return {key(k): camel(v) for k, v in value.items()}
    return value

source = json.loads((ROOT / 'data/bills.json').read_text())
if source['downloaded_at'][:10] != '2026-11-04':
    raise SystemExit('This editorial is dated 4 November 2026. Review its wording and date before regenerating against another snapshot.')
bills = {b['billId']: b for b in camel(source)['items']}
entries=[
(4297,'A licence to give you a short back and sides',
 'Would make registration compulsory for barbers and hairdressers in England.',
 'A country with an abundance of difficult problems has found another register to maintain: the people cutting its hair. The obvious editorial question is whether a haircut needs another compulsory administrative gateway.',
 'Consumer protection may justify standards. The long title alone does not establish what registration would cost or whether it would improve safety.'),
(4198,'The pond has entered the parliamentary process',
 'Would extend permitted development rights to wildlife ponds smaller than 0.2 hectares.',
 'National legislation for the right to dig a modest wildlife pond is a wonderfully British indication of how far planning bureaucracy can reach. The absurdity here is the apparent need for a parliamentary escape hatch.',
 'This proposal would relax planning restrictions. It would be misleading to describe it as a new pond ban or a new licensing scheme.'),
(4270,'A bill to make someone move a motion',
 'Would require the Leader of the House of Commons to move a motion prohibiting MPs from holding paid second jobs.',
 'Parliament proposes legislation requiring Parliament to propose a rule about Parliament. If procedural recursion were a public service, this would be exemplary delivery.',
 'The stated mechanism requires a motion; it is not itself a direct statutory prohibition on all second jobs. Supporters can reasonably argue that Commons rules are the appropriate route.'),
(4131,'Nature gets a tribunal',
 'Would recognise Nature as a legal subject, establish rights and duties, and create institutions including a Nature Guardianship Council, Bioregional Councils and a Nature’s Rights Tribunal.',
 'The ambition is ecological; the machinery is unmistakably administrative. The landscape gets rights, councils and its own tribunal. The satirical target is the proliferation of institutions, not the importance of protecting nature.',
 'Rights-of-nature approaches have a serious legal rationale. The title and long title are insufficient to judge the proposed institutions’ costs or effectiveness.'),
(4288,'Prohibit superintelligence; solve definitions later?',
 'Would prohibit development, deployment and operation of artificial superintelligence systems and establish monitoring and control powers.',
 'Few legislative titles offer a larger gap between the neatness of the prohibition and the difficulty of identifying, monitoring and controlling the thing being prohibited. That implementation problem is the editorial target.',
 'The long title does not tell us whether the full bill defines the threshold adequately. No claim is made that ordinary AI systems would be banned.'),
(4295,'Your imaginary digital double needs a statute',
 'Would regulate software and algorithms using personal data to model an individual’s preferences or behaviour, and provide rights concerning that data.',
 'The title sounds like Parliament has discovered that everyone has a spare person living in a computer. The serious question underneath the futuristic packaging is how this proposal would interact with existing data rights.',
 'Behavioural modelling and privacy harms are real. The evidence here supports a question about overlap, not a conclusion that the proposal is redundant.'),
(4309,'The national wet-wipe agenda',
 'Would make provision for wet-wipe marketing, advertising, sale and labelling.',
 'A dedicated bill for the marketing and labelling of wet wipes is an irresistible example of Parliament’s capacity to subdivide everyday life into legislative projects. Even the bathroom cupboard gets a programme of reform.',
 'Accurate labelling and environmental impacts can be legitimate concerns. This is not evidence that the bill would ban all wet wipes.'),
(4284,'Repeal, now with a sequel',
 'Would repeal the Climate Change Act 2008 and make consequential provision.',
 'The “No. 2” title supplies its own punchline: even wholesale repeal arrives as a sequel. The substantive editorial objection is the scale of what is proposed compared with the brevity of the stated purpose.',
 'The numbering alone does not establish why another version exists. Repeal is a political proposal, not an enacted change, and no impacts have been quantified here.'),
]
intro='An editorial shortlist for The Restorationist • Working year-end edition • 4 November 2026'
scope='This is an opinion-led selection, not an objective ranking. Selection favours unusually narrow regulation, elaborate administrative machinery, procedural recursion and sweeping proposals with obvious implementation questions. The summaries use Parliament’s bill titles, long titles and status metadata; they are not a clause-by-clause legal review.'
context='Andy Burnham became prime minister on 20 July 2026. These eight proposals have records updated during his tenure, but that does not establish that they were introduced during his tenure. All eight are private members’ bills, including the Lords proposal; none is a government bill. Labour sponsorship does not make a bill government policy. None of the eight was recorded as an Act in the retrieved records. The current-stage field can refer to a scheduled stage, not a completed debate.'
md=['# Parliament’s most ridiculous bills?\n',intro+'\n','## Read this first\n',scope+'\n',context+'\n','This snapshot is dated 4 November, not 31 December 2026. Refresh the dataset and review the shortlist after year-end.\n','Political context: [GOV.UK — Andy Burnham](https://www.gov.uk/government/people/andy-burnham).\n']
cards=[]
for n,(bid,heading,fact,verdict,caveat) in enumerate(entries,1):
 b=bills[bid]; assert b['billTypeId'] in (2, 5, 7, 8) and not b['isAct'], 'Re-review changed bill status';m=b['sponsors'][0]['member'];stage=b['currentStage']['description'];source=f'https://bills.parliament.uk/bills/{bid}';api=f'https://bills-api.parliament.uk/api/v1/Bills/{bid}'
 meta=f"{m['name']} · {m['party']} · {m['house']} · Current stage field: {stage} · Last update: {b['lastUpdate'][:10]}"
 md += [f'## {n}. {heading}\n',f"**{b['shortTitle']}**\n",meta+'\n','**Proposal:** '+fact+'\n','**Editorial verdict:** '+verdict+'\n','**Fair reading:** '+caveat+'\n',f'[Parliament bill page]({source}) · [API record]({api})\n']
 e=html.escape
 cards.append(f'<article><div class="number">{n:02}</div><h2>{e(heading)}</h2><h3>{e(b["shortTitle"])}</h3><p class="meta">{e(meta)}</p><p><strong>Proposal.</strong> {e(fact)}</p><p><strong>Editorial verdict.</strong> {e(verdict)}</p><p class="fair"><strong>Fair reading.</strong> {e(caveat)}</p><p><a href="{source}">Parliament bill page</a> · <a href="{api}">API record</a></p></article>')
md += ['## Sources and limits\n','Bill records retrieved directly from the UK Parliament Bills API on 4 November 2026. Sponsor, party, stage, bill type and Act status were checked for every selected bill. Source URLs are included with each entry. Titles are reproduced for identification; proposal descriptions are paraphrases. No misconduct, costs, vote outcomes or implementation effects are inferred from a title. This document is an editorial starting point and should be updated when the bills change.\n']
p=ROOT / 'public/reports'; p.mkdir(parents=True, exist_ok=True);(p/'ridiculous-bills-2026.md').write_text('\n'.join(md))
html_doc='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Parliament’s most ridiculous bills? — 2026</title><style>
:root{color-scheme:light}body{margin:0;background:#f6f3ed;color:#202c32;font:17px/1.65 Georgia,serif}main{max-width:840px;margin:50px auto;padding:0 26px}header{border-top:8px solid #a5412b;border-bottom:1px solid #d7cdc0;padding:25px 0}h1{font-size:clamp(38px,7vw,66px);line-height:1.08;letter-spacing:-2px;margin:18px 0}h2{font-size:29px;line-height:1.2;margin:8px 0 15px}h3{font:600 17px/1.5 system-ui}.kicker,.meta,.number,nav,footer{font-family:system-ui,sans-serif}.kicker,.number{color:#a5412b;font-size:13px;font-weight:700;letter-spacing:2px;text-transform:uppercase}.meta{font-size:13px;color:#5a6569}.scope{padding:22px 0;border-bottom:1px solid #d7cdc0;font-size:16px}article{padding:35px 0;border-bottom:1px solid #d7cdc0;break-inside:avoid}.fair{padding-left:18px;border-left:3px solid #c8bfb1;color:#4e5b5e}a{color:#94402c;text-underline-offset:3px}nav{font-size:13px;margin:20px 0}footer{font-size:13px;padding:25px 0 50px}@media print{body{background:white;font-size:11pt}main{margin:0;max-width:none}h1{font-size:36pt}h2{font-size:19pt}nav{display:none}a{color:inherit}article{padding:20px 0}@page{margin:18mm}}
</style></head><body><main><header><div class="kicker">The Restorationist · Parliament · 2026</div><h1>Parliament’s most<br>ridiculous bills?</h1><p>Eight proposals that invite a raised eyebrow — with the facts kept in view.</p><p class="meta">'''+html.escape(intro)+'''</p></header><nav><a href="ridiculous-bills-2026.md" download>Download Markdown document</a> · Use your browser’s Print command to save a PDF.</nav><section class="scope"><h2>Read this first</h2><p>'''+html.escape(scope)+'''</p><p>'''+html.escape(context)+'''</p><p>This is a <strong>4 November snapshot</strong>, not a completed 31 December review. Refresh and review after year-end. <a href="https://www.gov.uk/government/people/andy-burnham">Political context: GOV.UK</a>.</p></section>'''+''.join(cards)+'''<footer><strong>Sources and limits.</strong> Bill records retrieved directly from the UK Parliament Bills API on 4 November 2026. Sponsor, party, stage, bill type and Act status checked for each selected bill. Summaries paraphrase official long titles; this is not a clause-by-clause review. The selection makes no claims of misconduct, quantified costs or proven implementation effects. The document requires editorial review after each data refresh.</footer></main></body></html>'''
(p/'ridiculous-bills-2026.html').write_text(html_doc)
print('Created HTML and Markdown documents for 8 verified bills')
