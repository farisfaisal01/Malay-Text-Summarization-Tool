def tokenize_text(text):
    # Tokenize into sentences
    sentences = text.split(".")  # Split by period (adjust for more punctuation)
    
    # Tokenize each sentence into words
    tokenized_sentences = [sentence.split() for sentence in sentences]
    
    return tokenized_sentences  # List of tokenized sentences

def pos_tagging(tokenized_sentences):
    # Placeholder function for POS tagging; replace with an actual POS tagger later
    # Returns tuples of (word, POS) for each word in the sentence
    pos_tagged_sentences = []
    
    for sentence in tokenized_sentences:
        pos_tagged = [(word, "POS_TAG") for word in sentence]  # Dummy POS tags
        pos_tagged_sentences.append(pos_tagged)
    
    return pos_tagged_sentences

# Define a dictionary of common polysemous words with context clues for each sense
word_sense_dict = {
    "sewa": {
        "rent": ["tunggakan", "bayaran bulanan", "pembayaran", "perjanjian sewa", "penyewa"],
        "lease": ["perjanjian penyewaan", "kontrak", "sewaan kediaman"]
    },
    "penghuni": {
        "tenant": ["PPR", "bayar sewa", "penyewa", "golongan rentan", "penduduk"],
        "occupant": ["duduk", "tinggal", "mendiami"]
    },
    "tunggakan": {
        "arrears": ["bayaran bulanan", "gagal", "menjelaskan", "pembayaran", "kos tambahan"],
        "backlog": ["tertangguh", "ketinggalan", "kelewatan"]
    },
    "penyeliaan": {
        "maintenance": ["kemudahan", "penyelenggaraan", "membaik pulih", "kos", "persekitaran", "fungsi lif"],
        "supervision": ["pengawasan", "pemantauan"]
    },
    "perumahan": {
        "housing": ["Projek Perumahan Rakyat", "kediaman", "PPR", "penyewaan", "persekitaran", "unit"],
        "residence": ["rumah", "tempat tinggal", "kediaman"]
    },
    "kerajaan": {
        "government": ["KPKT", "subsidi", "peruntukan", "Dasar Komuniti Negara", "bantuan", "inisiatif"],
        "authority": ["agensi", "pihak berwajib", "peraturan"]
    },
    "pemaju": {
        "developer": ["projek perumahan", "pembangunan", "PPR", "perancangan", "penyeliaan"],
        "initiator": ["pembina", "syarikat pembangunan"]
    },
    "kos": {
        "cost": ["peruntukan", "subsidi", "bayaran sewa", "penyelenggaraan", "dana"],
        "price": ["harga", "yuran", "belanja"]
    },
    "perjanjian": {
        "agreement": ["penyewaan", "kontrak", "syarat", "terma", "penamatan"],
        "treaty": ["pakatan", "persetujuan"]
    },
    "penduduk": {
        "resident": ["PPR", "penyewa", "penghuni", "komuniti", "pendapatan rendah", "kehidupan"],
        "population": ["orang ramai", "masyarakat", "jumlah penduduk"]
    }
}

def disambiguate_word(word, context):
    if word in word_sense_dict:
        senses = word_sense_dict[word]
        
        # Look for clues in the context to pick the correct sense
        for sense, clues in senses.items():
            if any(clue in context for clue in clues):
                return sense  # Return the correct sense based on context clues
    
    return word  # Return the word itself if no disambiguation needed

def apply_wsd(tokenized_sentences):
    disambiguated_sentences = []
    
    for sentence in tokenized_sentences:
        context = " ".join([word for word, pos in sentence])  # Create context from sentence
        disambiguated_sentence = [(disambiguate_word(word, context), pos) for word, pos in sentence]
        disambiguated_sentences.append(disambiguated_sentence)
    
    return disambiguated_sentences

from collections import Counter

def calculate_tf(sentences):
    word_count = Counter()
    
    # Flatten the list of sentences into words
    for sentence in sentences:
        for word, pos in sentence:
            # Word with sense (if it's disambiguated)
            word_with_sense = word  # Default to word itself
            
            # If the word has a disambiguated sense, use it (e.g., "hak (rights)")
            if "(" in word and ")" in word:
                word_with_sense = word  # Use the disambiguated form
            
            word_count[word_with_sense] += 1
    
    return word_count

def display_word_counts(word_count):
    print("Word Counts (Term Frequency):")
    for word, count in word_count.items():
        print(f"{word}: {count}")
        
def score_sentences(sentences, tf_scores):
    scored_sentences = []
    
    for i, sentence in enumerate(sentences):
        score = 0
        for word, pos in sentence:
            score += tf_scores[word]  # Add TF score
        
        # Add a position-based bonus (earlier sentences get a higher score)
        position_score = max(1, len(sentences) - i)  # Basic position bonus
        score += position_score
        
        scored_sentences.append((score, sentence))
    
    return scored_sentences

def select_top_sentences(scored_sentences, summary_length):
    # Sort sentences by score (descending)
    scored_sentences.sort(reverse=True, key=lambda x: x[0])
    
    # Select the top N sentences based on summary length
    summary_sentences = scored_sentences[:summary_length]
    
    # Extract and return the original sentences (not the scores)
    return [" ".join([word for word, pos in sentence]) for _, sentence in summary_sentences]

def post_process_summary(selected_sentences):
    return ". ".join(selected_sentences) + "."

def extractive_summarization_pipeline(text, summary_length=5):
    # Step 1: Preprocess the text
    tokenized_sentences = tokenize_text(text)
    pos_tagged_sentences = pos_tagging(tokenized_sentences)
    
    # Step 2: Apply Word Sense Disambiguation (WSD)
    disambiguated_sentences = apply_wsd(pos_tagged_sentences)
    
    # Step 3: Score the sentences
    tf_scores = calculate_tf(disambiguated_sentences)
    
    # Display word counts before moving forward
    display_word_counts(tf_scores)
    
    scored_sentences = score_sentences(disambiguated_sentences, tf_scores)
    
    # Step 4: Select the top sentences
    selected_sentences = select_top_sentences(scored_sentences, summary_length)
    
    # Step 5: Post-process and return the summary
    summary = post_process_summary(selected_sentences)
    
    return summary

summary = extractive_summarization_pipeline("""Ketiadaan sumber kewangan yang stabil akibat kegagalan penghuni Projek Perumahan Rakyat menjelaskan sewa unit masing-masing, menyukarkan pihak berkaitan menyediakan kemudahan terbaik buat penduduk, sekali gus membantutkan usaha kerajaan untuk mewujudkan perumahan berdaya saing. 
Artikel terakhir daripada laporan dua bahagian ini berkongsi tentang usaha yang diambil oleh Kementerian Perumahan dan Kerajaan Tempatan bagi menangani kedua-dua isu berbangkit. 
       
Masalah tunggakan sewa Projek Perumahan Rakyat (PPR) yang dilihat kian meruncing sejak belakangan ini, mendatangkan natijah buruk kepada penduduk perumahan itu sendiri.
Tanpa sumber kewangan yang stabil akibat kegagalan penghuni membayar sewa mereka, agensi pengurus perumahan itu mungkin tidak mampu menyediakan persekitaran yang selesa buat penduduk seperti memastikan lif berfungsi dengan baik.
Akan tetapi, “selesa” duduk secara percuma lantaran tiada tindakan tegas diambil oleh pihak berwajib ke atas mereka yang culas membayar sewa, membuatkan masalah ini terus berlarutan.  
Sedar akan hakikat itu serta implikasi kewangan ke atas kerajaan yang ditanggung selama ini, Kementerian Perumahan dan Kerajaan Tempatan (KPKT) memberitahu Bernama yang ia berhasrat mengambil pendekatan lebih proaktif, termasuk menggubal undang-undang baharu yang akan memberi situasi menang-menang kepada penyewa dan juga agensi pengurus PPR. 
 
TANGGUNG KOS
Menjawab soalan yang dikemukakan oleh Bernama kepadanya, KPKT mengakui sikap culas penghuni PPR membayar sewa menyebabkan kerajaan menanggung kos tambahan bagi menyelia dan menyelenggara kemudahan yang disediakan di perumahan itu. 

“Penyediaan PPR pada dasarnya adalah untuk membantu golongan berpendapatan rendah mendiami rumah yang selesa. Justeru,  program perumahan ini hanya mengenakan kadar sewa minimum berbanding kadar sewa perumahan lain yang jauh lebih tinggi.
“… apabila berlaku pula tunggakan sewa, kerajaan terpaksa mengeluarkan dana berasingan bagi tujuan penyelenggaraan perumahan itu termasuklah pembaikan lif, dan keadaan ini juga akan memberi kesan kepada hasil kerajaan,” jelas KPKT dalam jawapan bertulis kepada Bernama.
Untuk rekod, sebanyak RM500 juta diperuntukkan di bawah Rancangan Malaysia ke-12,  bagi menyelenggara serta membaik pulih perumahan awam berstrata di seluruh negara yang turut merangkumi PPR, melalui Program Penyelenggaraan Perumahan.
Menurut KPKT lagi, setakat Disember tahun lalu, terdapat 161 PPR telah siap dibina di seluruh negara, dan daripada jumlah itu, sebanyak 21 projek diselia sepenuhnya oleh kementerian berkenaan.
Yang lain diuruskan secara langsung oleh kerajaan negeri dan Pihak Berkuasa Tempatan.
“Daripada 21 PPR yang diselia oleh KPKT ini,  hanya dua buah yang ditawarkan di bawah skim PPR sewa manakala selebihnya di bawah skim PPR dimiliki.
“Berdasarkan data kutipan sewa dua PPR ini pula, iaitu PPR Pasir Mas di Kelantan dan PPR Lembah Subang 1 di Selangor, jumlah tunggakan yang direkodkan setakat ini adalah sekitar RM12 juta,” kata kementerian itu.
Skim PPR sewa diperkenalkan pada Februari 2002 bagi memenuhi keperluan penduduk setinggan yang ditempatkan semula serta golongan berpendapatan rendah.
 
DIKENAKAN TINDAKAN
Menurut KPKT, pihaknya boleh menamatkan perjanjian penyewaan perumahan itu jika penghuni PPR berkenaan gagal atau culas dalam melunaskan bayaran sewa.

“Bagi perjanjian penyewaan di bawah PPR seliaan KPKT, terma melibatkan obligasi penyewa serta penamatan penyewaan jelas dinyatakan, iaitu jika penyewa gagal menjelaskan kadar sewa tiga bulan berturut-turut atau pada satu-satu masa, KPKT perlu  memberikan notis (peringatan), dan sekiranya masih gagal menyelesaikan (tunggakan) dalam  tempoh yang ditetapkan, perjanjian penyewaan tersebut boleh ditamatkan,” jelas kementerian itu.
Akan tetapi, KPKT berkata sebarang tindakan drastik yang boleh menjejaskan penghuni perlu diteliti dengan mengambil kira banyak aspek memandangkan golongan yang mendiami PPR adalah kelompok rentan yang kebanyakannya mempunyai masalah sumber pendapatan.
Dalam pada itu,  KPKT sedang meneliti keperluan memasukkan skop perumahan awam termasuk PPR dalam Rang Undang-Undang Sewaan Kediaman yang sedang digubal.
“KPKT akan meneruskan sesi libat urus dengan pihak berkaitan bagi memuktamadkan draf rang undang-undang ini, khususnya dari segi pelaksanaan dan pentadbiran undang-undang itu.
“Maklum balas dan pandangan yang diterima hasil libat urus ini akan diambil kira dalam menambah baik draf perundangan ini  agar kepentingan semua pihak dipelihara,” tambah KPKT.
Sebelum ini, Menteri Perumahan dan Kerajaan Tempatan Nga Kor Ming dilaporkan berkata perundangan yang sedang digubal itu bersifat neutral dan mengambil kira kepentingan kedua-dua pihak, iaitu pemilik dan penyewa. 
Perundangan ini  akan melindungi kepentingan serta hak penyewa dan pemilik kediaman yang ketika ini hanya dilindungi melalui Akta Kontrak 1950 yang bersifat umum dan tidak menyeluruh.
 
DASAR KOMUNITI NEGARA
Selain mengambil tindakan tegas atau undang-undang terhadap penduduk culas bayar sewa, kerajaan juga melaksanakan program berbentuk intervensi seperti mengupayakan komuniti dengan aspek kesihatan dan keselamatan, memupuk perasaan keterangkuman (sense of ownership) dan semangat kejiranan seperti hormat-menghormati sesama sendiri. 

“Ini termasuk melaksanakan Dasar Komuniti Negara (DKomN) yang bertujuan  menangani isu-isu perumahan di peringkat komuniti setempat,  khususnya di  kawasan perumahan strata di seluruh negara.
“Menerusi program ini, pada tahun lalu, semua bakal penghuni PPR perlu menghadiri kursus kesedaran sivik yang bertujuan meningkatkan kesedaran sivik dalam  kalangan penghuni, meningkatkan tanggungjawab dalam aspek kebersihan  persekitaran, penyelenggaraan dan penggunaan harta bersama di PPR,” kata KPKT.
Pada masa sama, kementerian turut mengingatkan penghuni agar melaksanakan tanggungjawab memastikan sewa bulanan dijelaskan mengikut tempoh yang ditetapkan.
“Penghuni seharusnya mematuhi syarat yang telah dipersetujui dalam perjanjian penyewaan perumahan berkenaan.
“Setiap penyewa perlu sedar bahawa mereka  merupakan golongan yang mendapat banyak manfaat daripada inisiatif ini, dengan kerajaan telah membelanjakan sejumlah besar (peruntukan) subsidi bagi membangunkan perumahan ini,” tegas KPKT.""")
print(summary)
