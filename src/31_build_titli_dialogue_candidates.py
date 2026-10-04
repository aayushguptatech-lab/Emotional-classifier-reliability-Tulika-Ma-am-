from collections import Counter
import csv
import hashlib
from pathlib import Path
import random
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data" / "cleaned" / "hindi" / "titli_clean.txt"
OUTPUT_DIR = ROOT / "data" / "extracted" / "hindi" / "titli"
CSV_OUTPUT = OUTPUT_DIR / "titli_dialogue_candidates.csv"
REPORT_OUTPUT = OUTPUT_DIR / "titli_candidate_extraction_validation.txt"

EXPECTED_SECTIONS = [
	"1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8",
	"2.1", "2.2", "2.3", "2.4", "2.5", "2.9", "2.10",
	"3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7", "3.8",
	"4.1", "4.2", "4.3", "4.4", "4.5",
]
EXPECTED_PARAGRAPHS = 1406
SECTION_HEADER = re.compile(
	r"^===== TITLI SECTION ([0-9]+\.[0-9]+) \| SOURCE (.+?) =====$"
)

SPEECH_VERB = re.compile(
	r"(?:"
	r"उत्तर\s+(?:में\s+)?(?:दिया|दिया|देता|देती|देते|कहा)|"
	r"जवाब\s+(?:दिया|देता|देती|देते)|"
	r"कहने\s+(?:लगा|लगी|लगे)|"
	r"बोल\s+उठा|बोल\s+उठी|बोल\s+उठे|"
	r"कहते\s+हुए|कहती\s+हुई|कहता\s+हुआ|"
	r"पूछकर|कहकर|पुकारकर|उत्तर\s+में\s+कहा|"
	r"चिल्लाया|चिल्लाई|चिल्लाए|फुसफुसाया|फुसफुसाई|"
	r"समझाया|समझाई|बताया|बतायी|बताई|बताए|पुकारा|"
	r"बोला|बोली|बोले|पूछा|पूछी|पूछे|कहा|कही|कहे|"
	r"कहता|कहती|कहते|बोलता|बोलती|बोलते|पूछता|पूछती|पूछते"
	r")(?![ँािीुूृेैोौंः])"
)
ATTRIBUTION_ACTOR = re.compile(
	r"(?P<actor>[\u0900-\u097f]+)\s+ने(?:\s+[\u0900-\u097f]+){0,4}\s*$"
)
ATTRIBUTION_DELIMITER = re.compile(r"\s*[:,]?\s*[—–-]\s*")
QUOTE_PAIRS = (("“", "”"), ("‘", "’"), ("「", "」"), ('"', '"'), ("'", "'"))
NARRATIVE_CONTINUATION = re.compile(
	r"(?P<separator>(?:[.!?।॥][”’\"']?\s+|_{2,}\s*))"
	r"(?P<narrative>(?:सहसा|अचानक|इतने में|कुछ देर बाद|उसके मन में|उसके हृदय में|"
	r"मधुबन|शैला|बंजो|इन्द्रदेव|इंद्रदेव|चौबेजी|राजकुमारी|तितली|अनवरी|माधुरी|"
	r"श्यामदुलारी|वह|वे|उसने|उन्होंने|उसकी|उसके)\s+"
	r"(?:चुप|सोच|बैठ|देख|चल|हंस|रो|उठ|लौट|मुड़|मुस्करा|आंख|मन|हृदय|"
	r"कहने लगा|कहने लगी|कहने लगे|उसी दिन से|मेस में|रहने लगी|रहने लगा|"
	r"रुककर|नहाने लगा|नहाने लगी|देखने लगा|देखने लगी|सोचने लगा|सोचने लगी|"
	r"बाहर चले|चले गए|चली गई|घूम पड़ी|घूम पड़ा|आकर खड़े हो गए|खड़े हो गए|"
	r"के साथ घूम|भीतर चला|भीतर चली|लौट आया|लौट आई)|दोनों की|"
	r"(?:(?:मधुबन|शैला|बंजो|इन्द्रदेव|इंद्रदेव|चौबेजी|राजकुमारी|तितली|अनवरी|"
	r"माधुरी|श्यामदुलारी|वह|वे|उसने|उन्होंने)\s+[^.!?।]{0,45}?"
	r"(?:बाहर चले गए|चले गए|चली गई|घूम पड़ी|घूम पड़ा|आकर खड़े हो गए|"
	r"खड़े हो गए|नमस्कार किया|प्रसन्न हुई|प्रसन्न हो गई|नहाने चली गई|"
	r"नहाने चला गया|बात बदल दी|चलने लगी|चलने लगा|बैठ गई|बैठ गया|"
	r"ले आया|ले आई|लेकर आया|लेकर आई|बीच में बोल उठे)))"
)
REJECTED_CONTENT = Counter()

GENERIC_ACTORS = {
	"मैं", "वह", "वे", "यह", "ये", "एक", "उस", "उसने", "उसकी", "उसके",
	"सब", "कोई", "किसी", "लोग", "लड़की", "लड़का", "स्त्री", "पुरुष",
	"बुड्ढे", "बुड्ढा", "बुड्ढी", "आदमी", "व्यक्ति", "किसान", "साहब",
	"साहबों", "बाबाजी", "नौकर", "मालकिन", "सरकार", "कहते", "कहकर",
}
INTERFACE_PATTERNS = (
	re.compile(r"<\s*/?\s*[a-z][^>]*>", re.IGNORECASE),
	re.compile(r"(?:सामग्री पर जाएँ|मुख्य मेन्यू|साइडबार पर ले जाएँ|खोजें|दिखावट|दान करें|खाता बनाएँ|लॉग-इन करें|मुखपृष्ठ|हाल की घटनाएँ|हाल में हुए परिवर्तन)"),
)
NARRATIVE_START = re.compile(
	r"^(?:सहसा|अचानक|इतने में|कुछ देर बाद|उसके मन में|उसके हृदय में|"
	r"अंधकार|प्रकाश|वह(?:ने)?\s+(?:देखा|सोचा|चलने लगा|चलने लगी|बैठ गया|बैठ गई))"
)
SPOKEN_CUE = re.compile(
	r"[?？!！]|(?:अरे|अहो|हां|हाँ|नहीं|बापू|मालकिन|भैया|दादा|"
	r"अच्छा|चलो|ठीक|जी|सरकार|देखो|क्यों|क्या)"
)
SPOKEN_START = re.compile(
	r"^(?:क्या|क्यों|कहां|कहाँ|कौन|कब|कैसे|कितना|अरे|अहो|हां|हाँ|नहीं|"
	r"बापू|मालकिन|भैया|दादा|अच्छा|चलो|ठीक|जी|सरकार|देखो|मैं|मुझे|मेरा|"
	r"मेरे|हम|हमारा|हमारे|तुम|तुम्हारा|तुम्हारे|आप|आपका|आपके)"
)


def parse_source(text):
	sections = []
	current = None
	paragraph_index = 0

	for raw_line in text.splitlines():
		line = raw_line.strip()
		if not line:
			continue

		match = SECTION_HEADER.fullmatch(line)
		if match:
			current = {
				"section": match.group(1),
				"source_file": match.group(2),
				"paragraphs": [],
			}
			sections.append(current)
			continue

		if current is None:
			raise ValueError("Text found before the first Titli section header")

		paragraph_index += 1
		current["paragraphs"].append(
			{
				"section": current["section"],
				"source_file": current["source_file"],
				"source_paragraph": line,
				"source_paragraph_index": paragraph_index,
			}
		)

	return sections


def find_attributions(paragraph):
	anchors = []
	for match in SPEECH_VERB.finditer(paragraph):
		prefix_start = max(0, match.start() - 55)
		prefix = paragraph[prefix_start:match.start()]
		actor_match = ATTRIBUTION_ACTOR.search(prefix)
		if actor_match:
			actor = actor_match.group("actor")
			anchor_start = prefix_start + actor_match.start("actor")
			attribution_text = paragraph[anchor_start:match.end()]
			explicit_actor = True
		else:
			actor = ""
			anchor_start = match.start()
			attribution_text = paragraph[match.start():match.end()]
			explicit_actor = False

		name_candidate = actor if actor and actor not in GENERIC_ACTORS else ""
		anchors.append(
			{
				"start": match.start(),
				"end": match.end(),
				"anchor_start": anchor_start,
				"verb": match.group(0),
				"attribution_text": attribution_text,
				"name_candidate": name_candidate,
				"explicit_actor": explicit_actor,
			}
		)
	return anchors


def find_quote_spans(paragraph):
	spans = []
	for opening, closing in QUOTE_PAIRS:
		search_from = 0
		while search_from < len(paragraph):
			open_at = paragraph.find(opening, search_from)
			if open_at < 0:
				break
			close_at = paragraph.find(closing, open_at + len(opening))
			if close_at < 0:
				break
			start = open_at + len(opening)
			end = close_at
			if end > start:
				spans.append((start, end, open_at, close_at + len(closing)))
			search_from = close_at + len(closing)
	return sorted(spans)


def actor_for_quote(quote, anchors):
	start, end, open_at, close_end = quote
	nearby = [
		anchor for anchor in anchors
		if (anchor["end"] <= open_at and open_at - anchor["end"] <= 45)
		or (anchor["anchor_start"] >= close_end and anchor["anchor_start"] - close_end <= 55)
	]
	if not nearby:
		return None
	return min(
		nearby,
		key=lambda anchor: min(
			abs(open_at - anchor["end"]), abs(anchor["anchor_start"] - close_end)
		),
	)


def trim_span(paragraph, start, end):
	while start < end and paragraph[start].isspace():
		start += 1
	while end > start and paragraph[end - 1].isspace():
		end -= 1
	return start, end


def is_interface_or_markup(text):
	return any(pattern.search(text) for pattern in INTERFACE_PATTERNS)


def is_obvious_narrative(text):
	normalized = text.strip(" \t—–-:;,")
	return bool(NARRATIVE_START.search(normalized) and not SPOKEN_CUE.search(normalized))


def candidate_record(source_item, start, end, method, anchor=None, quote=False):
	paragraph = source_item["source_paragraph"]
	start, end = trim_span(paragraph, start, end)
	dialogue = paragraph[start:end]
	if not dialogue:
		REJECTED_CONTENT["empty"] += 1
		return None
	if is_interface_or_markup(dialogue):
		REJECTED_CONTENT["interface"] += 1
		return None
	if is_obvious_narrative(dialogue):
		REJECTED_CONTENT["narrative"] += 1
		return None

	attribution_text = anchor["attribution_text"] if anchor else ""
	reason_parts = []
	if not quote:
		boundary = NARRATIVE_CONTINUATION.search(dialogue)
		if boundary:
			end = start + boundary.start("narrative")
			start, end = trim_span(paragraph, start, end)
			dialogue = paragraph[start:end]
			reason_parts.append("stopped before a recognizable narrative continuation; review boundary")
	if len(dialogue) > 500:
		reason_parts.append("unusually long candidate (>500 characters); review boundaries")
	if len(dialogue) < 5 and not SPOKEN_CUE.search(dialogue):
		reason_parts.append("very short candidate (<5 characters); verify spoken context")
	if not attribution_text:
		reason_parts.append("speaker attribution unresolved")

	return {
		"section": source_item["section"],
		"source_file": source_item["source_file"],
		"source_paragraph": paragraph,
		"source_paragraph_index": source_item["source_paragraph_index"],
		"detection_method": method,
		"dialogue_text": dialogue,
		"attribution_text": attribution_text,
		"attribution_name_candidate": anchor["name_candidate"] if anchor else "",
		"source_start": start,
		"source_end": end,
		"confidence": "high" if attribution_text else "medium",
		"review_reason": "; ".join(reason_parts),
	}


def extract_from_paragraph(source_item):
	paragraph = source_item["source_paragraph"]
	anchors = find_attributions(paragraph)
	quotes = find_quote_spans(paragraph)
	found = []

	for quote in quotes:
		start, end, open_at, close_end = quote
		quote_text = paragraph[start:end]
		anchor = actor_for_quote(quote, anchors)
		has_speech_punctuation = bool(re.search(r"[?？!！।]", quote_text))
		if not anchor and not has_speech_punctuation:
			continue
		method = "attribution_quote" if anchor else "unattributed_quote"
		record = candidate_record(source_item, start, end, method, anchor)
		if record:
			found.append(record)

	for anchor_index, anchor in enumerate(anchors):
		delimiter = ATTRIBUTION_DELIMITER.match(paragraph, anchor["end"])
		if delimiter:
			start = delimiter.end()
			while start < len(paragraph) and paragraph[start] in "\"'“‘「":
				start += 1

			if not any(q[0] <= start <= q[1] for q in quotes):
				next_anchor = next(
					(item for item in anchors[anchor_index + 1:] if item["anchor_start"] > start),
					None,
				)
				end = next_anchor["anchor_start"] if next_anchor else len(paragraph)
				while end > start and paragraph[end - 1] in " \t—–-:,;":
					end -= 1

				if start < end:
					method = "multi_turn_paragraph" if next_anchor else "attribution_dash"
					record = candidate_record(source_item, start, end, method, anchor)
					if record:
						found.append(record)

		prefix = paragraph[:anchor["anchor_start"]]
		trailing_dash = re.search(r"[—–-]\s*$", prefix)
		if trailing_dash and anchor["explicit_actor"]:
			prior_starts = []
			for previous_anchor in anchors[:anchor_index]:
				previous_delimiter = ATTRIBUTION_DELIMITER.match(
					paragraph, previous_anchor["end"]
				)
				if previous_delimiter and previous_delimiter.end() <= trailing_dash.start():
					prior_starts.append(previous_delimiter.end())

			start = prior_starts[-1] if prior_starts else 0
			spoken_prefix = paragraph[start:trailing_dash.start()]
			if start > 0 or len(spoken_prefix.strip()) <= 100 or SPOKEN_START.match(spoken_prefix.lstrip()):
				record = candidate_record(
					source_item, start, trailing_dash.start(), "attribution_dash", anchor
				)
				if record:
					found.append(record)

	preference = {
		"attribution_quote": 0,
		"attribution_dash": 1,
		"multi_turn_paragraph": 2,
		"unattributed_quote": 3,
		"named_dash": 4,
		"quoted_speech": 5,
		"other_conservative_speech": 6,
	}
	by_span = {}
	for record in found:
		key = (record["source_start"], record["source_end"])
		if key not in by_span or preference[record["detection_method"]] < preference[by_span[key]["detection_method"]]:
			by_span[key] = record

	return sorted(by_span.values(), key=lambda item: (item["source_start"], item["source_end"]))


def stable_sample(records, sample_size=100):
	if len(records) <= sample_size:
		return list(records)
	rng = random.Random(3101)
	return [records[index] for index in sorted(rng.sample(range(len(records)), sample_size))]


def format_counter(counter, keys=None):
	if keys is None:
		keys = sorted(counter)
	return "\n".join(f"  {key}: {counter.get(key, 0)}" for key in keys)


def main():
	if hasattr(sys.stdout, "reconfigure"):
		sys.stdout.reconfigure(encoding="utf-8")

	source_bytes = SOURCE.read_bytes()
	source_text = source_bytes.decode("utf-8")
	sections = parse_source(source_text)
	detected_sections = [section["section"] for section in sections]
	paragraphs = [item for section in sections for item in section["paragraphs"]]

	candidates = []
	for source_item in paragraphs:
		candidates.extend(extract_from_paragraph(source_item))

	candidates.sort(
		key=lambda item: (
			item["source_paragraph_index"], item["source_start"], item["source_end"]
		)
	)
	for index, candidate in enumerate(candidates, start=1):
		candidate["candidate_id"] = f"TITLI-CAND-{index:06d}"

	output_fields = [
		"candidate_id", "section", "source_file", "source_paragraph",
		"source_paragraph_index", "detection_method", "dialogue_text",
		"attribution_text", "attribution_name_candidate", "source_start",
		"source_end", "confidence", "review_reason",
	]
	OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
	with CSV_OUTPUT.open("w", encoding="utf-8", newline="") as csv_file:
		writer = csv.DictWriter(
			csv_file, fieldnames=output_fields, lineterminator="\n"
		)
		writer.writeheader()
		for candidate in candidates:
			writer.writerow({field: candidate[field] for field in output_fields})

	with CSV_OUTPUT.open("r", encoding="utf-8", newline="") as csv_file:
		emitted_candidates = list(csv.DictReader(csv_file))

	methods = Counter(item["detection_method"] for item in candidates)
	by_section = Counter(item["section"] for item in candidates)
	duplicate_ids = len(candidates) - len({item["candidate_id"] for item in candidates})
	with_attribution = sum(bool(item["attribution_text"]) for item in candidates)
	unresolved = len(candidates) - with_attribution
	long_candidates = sum(len(item["dialogue_text"]) > 500 for item in candidates)
	short_candidates = sum(len(item["dialogue_text"]) < 5 for item in candidates)
	empty_dialogue = sum(not item["dialogue_text"] for item in candidates)
	narrative_contamination = sum(is_obvious_narrative(item["dialogue_text"]) for item in candidates)
	interface_contamination = sum(is_interface_or_markup(item["dialogue_text"]) for item in candidates)
	narrative_boundary_cuts = sum(
		"stopped before a recognizable narrative continuation" in item["review_reason"]
		for item in candidates
	)

	source_paragraphs_by_index = {
		item["source_paragraph_index"]: item["source_paragraph"] for item in paragraphs
	}
	sample = stable_sample(emitted_candidates)
	mismatches = [
		item["candidate_id"] for item in sample
		if (
			source_paragraphs_by_index.get(int(item["source_paragraph_index"]))
			!= item["source_paragraph"]
			or item["source_paragraph"][int(item["source_start"]):int(item["source_end"])]
			!= item["dialogue_text"]
		)
	]

	missing_sections = [item for item in EXPECTED_SECTIONS if item not in detected_sections]
	unexpected_sections = [item for item in detected_sections if item not in EXPECTED_SECTIONS]
	validation_errors = []
	if detected_sections != EXPECTED_SECTIONS:
		validation_errors.append("Detected section order does not match the expected canonical order")
	if len(paragraphs) != EXPECTED_PARAGRAPHS:
		validation_errors.append(
			f"Expected {EXPECTED_PARAGRAPHS} canonical paragraphs; found {len(paragraphs)}"
		)
	if len(emitted_candidates) != len(candidates):
		validation_errors.append("Serialized CSV row count does not match generated candidate count")
	if duplicate_ids:
		validation_errors.append("Duplicate candidate IDs detected")
	if mismatches:
		validation_errors.append("Provenance substring mismatches detected")
	if empty_dialogue:
		validation_errors.append("Empty dialogue candidates detected")
	if narrative_contamination or interface_contamination:
		validation_errors.append("Contamination detected in emitted candidates")

	status = "PASS" if not validation_errors else "FAIL"
	report = [
		"TITLI HINDI DIALOGUE CANDIDATE EXTRACTION VALIDATION",
		"=" * 72,
		f"Source path: {SOURCE.relative_to(ROOT).as_posix()}",
		f"Source SHA256: {hashlib.sha256(source_bytes).hexdigest()}",
		f"Sections detected: {', '.join(detected_sections)}",
		f"Expected sections: {', '.join(EXPECTED_SECTIONS)}",
		f"Missing sections: {', '.join(missing_sections) if missing_sections else 'None'}",
		f"Unexpected sections: {', '.join(unexpected_sections) if unexpected_sections else 'None'}",
		f"Total source paragraphs: {len(paragraphs)}",
		f"Total candidates: {len(candidates)}",
		"Candidates by detection method:",
		format_counter(methods, [
			"attribution_dash", "attribution_quote", "named_dash", "quoted_speech",
			"multi_turn_paragraph", "unattributed_quote", "other_conservative_speech",
		]),
		"Candidates by section:",
		format_counter(by_section, EXPECTED_SECTIONS),
		f"Candidates with attribution evidence: {with_attribution}",
		f"Unresolved candidates: {unresolved}",
		f"Candidates >500 characters: {long_candidates}",
		f"Candidates <5 characters: {short_candidates}",
		f"Duplicate candidate IDs: {duplicate_ids}",
		f"Provenance verification sample size: {len(sample)}",
		f"Provenance mismatches: {len(mismatches)}",
		f"Obvious narrative contamination count: {narrative_contamination}",
		f"Narrative-only candidate spans rejected: {REJECTED_CONTENT['narrative']}",
		f"Narrative boundary cuts flagged for review: {narrative_boundary_cuts}",
		f"Interface contamination count: {interface_contamination}",
		f"Interface-only candidate spans rejected: {REJECTED_CONTENT['interface']}",
		f"Empty dialogue count: {empty_dialogue}",
		f"Final validation status: {status}",
		"",
		"Validation details:",
		*(
			[f"- {error}" for error in validation_errors]
			if validation_errors
			else ["- All required structural and provenance checks passed."]
		),
		"",
		"Detection note: speaker labels are not assigned; attribution_name_candidate only copies an explicit nearby Hindi attribution token.",
	]
	REPORT_OUTPUT.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")

	print(f"Titli sections: {len(detected_sections)}; source paragraphs: {len(paragraphs)}")
	print(f"Dialogue candidates: {len(candidates)}")
	print("Detection methods: " + ", ".join(f"{key}={methods.get(key, 0)}" for key in sorted(methods)))
	print(f"Provenance: {len(sample)} sampled, {len(mismatches)} mismatches")
	print(
		"Contamination: "
		f"narrative={narrative_contamination}, interface={interface_contamination}, empty={empty_dialogue}; "
		f"narrative-only rejected={REJECTED_CONTENT['narrative']}, boundary cuts={narrative_boundary_cuts}"
	)
	print(f"Validation: {status}")
	if validation_errors:
		raise SystemExit("; ".join(validation_errors))


if __name__ == "__main__":
	main()
