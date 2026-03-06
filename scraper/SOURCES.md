# Legal Data Sources - Verified Working URLs

Tested from server (non-Thailand IP) on 2026-03-07.

## DOWNLOAD OK - พร้อมใช้งาน

### 1. Hugging Face Datasets

| Dataset | Content | Size | License | URL |
|---------|---------|------|---------|-----|
| pythainlp/thailaw | พ.ร.บ. ทั้งหมด 42,755 ฉบับ (จาก krisdika.go.th) | 191 MB | Public Domain (CC0) | https://huggingface.co/datasets/pythainlp/thailaw |
| pythainlp/thailaw-v1.0 | พ.ร.บ. 52,600 ฉบับ (รวม law.go.th) | - | Public Domain | https://huggingface.co/datasets/pythainlp/thailaw-v1.0 |
| airesearch/WangchanX-Legal-ThaiCCL-RAG | Legal Q&A + contexts จาก 35 พ.ร.บ. (11,953 rows) | 21 MB | MIT | https://huggingface.co/datasets/airesearch/WangchanX-Legal-ThaiCCL-RAG |
| obbzung/soc-ratchakitcha | ราชกิจจานุเบกษา metadata + OCR (1M+ docs, ตั้งแต่ 2428) | 170+ GB | CC-BY-4.0 | https://huggingface.co/datasets/obbzung/soc-ratchakitcha |

### 2. GitHub Datasets

| Dataset | Content | Size | License | URL |
|---------|---------|------|---------|-----|
| PyThaiNLP/thai-law (ป.พ.พ.) | ประมวลกฎหมายแพ่งและพาณิชย์ 1,911 มาตรา | 1.5 MB | Public Domain | https://github.com/PyThaiNLP/thai-law/releases/download/civil-commercial-csv-v0.1/civil-and-commercial-datasets.csv |
| PyThaiNLP/thai-law (ป.อาญา) | ประมวลกฎหมายอาญา 457 มาตรา | 0.5 MB | Public Domain | https://github.com/PyThaiNLP/thai-law/releases/download/criminal-csv-v0.1/criminal-datasets.csv |
| PyThaiNLP/thai-law (ทุกฉบับ) | กฎหมายทั้งหมด 42,755 ฉบับ (CSV) | 807 MB | Public Domain | https://github.com/PyThaiNLP/thai-law/releases/download/v0.2/law.csv |
| PyThaiNLP/thai-law (โรคติดต่อ) | พ.ร.บ.โรคติดต่อ | 0.1 MB | Public Domain | https://github.com/PyThaiNLP/thai-law/releases/download/communicable-diseases-csv-v0.1/communicable-diseases-datasets.csv |
| KevinMercury/tscc-dataset | ฎีกาอาญา 1,000 คดี (1,207 ประเด็น) | 0.9 MB | Academic | https://github.com/KevinMercury/tscc-dataset |

### 3. Websites (Scraping)

| Site | Content | Status | URL |
|------|---------|--------|-----|
| library.siam-legal.com | ป.พ.พ. + ป.อาญา (EN+TH), แบ่งตาม section | OK 200 | https://library.siam-legal.com/thai-civil-and-commercial-code/ |
| ocs.go.th (กฤษฎีกา) | ฐานข้อมูลกฎหมาย, ค้นหาได้ | OK 200 | https://www.ocs.go.th/searchlaw |
| lawyerscouncil.or.th | สภาทนายความ, ข่าว/บทความ | OK 200 | https://lawyerscouncil.or.th/ |

## BLOCKED - เข้าไม่ได้จาก server ต่างประเทศ

| Site | Content | Status | Note |
|------|---------|--------|------|
| deka.supremecourt.or.th | ฎีกาทางการ (ค้นหา) | Timeout | ต้อง scrape จากเครื่องในไทย |
| deka.in.th | ฎีกา (รวบรวม) | Connection refused | ต้อง scrape จากเครื่องในไทย |
| decision.coj.go.th | คำพิพากษาศาลยุติธรรม | Timeout | ต้อง scrape จากเครื่องในไทย |
| ratchakitcha.soc.go.th | ราชกิจจานุเบกษา (ต้นฉบับ) | 403 Cloudflare | ใช้ HF dataset แทน |
| law.go.th | ฐานข้อมูลกฎหมาย | 403 Forbidden | ใช้ HF/GitHub dataset แทน |
| lawsiam.com | รวมฎีกา/กฎหมาย | 403 Forbidden | - |
| ilawclub.com | บทความกฎหมาย | Timeout | - |

## Data Format Summary

| แหล่ง | Format | Fields |
|-------|--------|--------|
| pythainlp/thailaw | Parquet | sysid, title, txt |
| WangchanX-Legal-RAG | Parquet | question, positive_contexts, positive_answer |
| soc-ratchakitcha | JSONL | no, doctitle, bookNo, section, category, publishDate, pdf_file |
| PyThaiNLP CSV (ป.พ.พ./ป.อาญา) | CSV | article, text, notes |
| TSCC | CSV | dekaid, year, category, fact, decision, lawids, isguilty |
