"""オフライン用フレーズ集のデータ（手書き）。
`python tools/build_phrasebook.py` で static/phrasebook/*.json に書き出す。
ここに無い言語は `python tools/generate_phrasebook.py`（Gemini）で作れる。
※ ネイティブの方に確認してもらうと安心です（直接このファイルか JSON を直して構いません）。"""

# (カテゴリID, 日本語名, 英語名, [(フレーズID, 日本語, 英語), ...])
CATEGORIES = [
    ("basic", "あいさつ・基本", "Basics", [
        ("hello", "こんにちは", "Hello"),
        ("thanks", "ありがとうございます", "Thank you very much"),
        ("excuse", "すみません（呼びかけ）", "Excuse me"),
        ("sorry", "ごめんなさい", "I'm sorry"),
        ("dontunderstand", "わかりません", "I don't understand"),
        ("slowly", "もう少しゆっくり話してください", "Could you speak more slowly, please?"),
    ]),
    ("food", "食事", "Food", [
        ("table2", "2人です", "A table for two, please"),
        ("menu", "メニューを見せてください", "Can I see the menu, please?"),
        ("recommend", "おすすめは何ですか？", "What do you recommend?"),
        ("allergy", "ピーナッツアレルギーです", "I'm allergic to peanuts"),
        ("check", "お会計をお願いします", "The check, please"),
        ("delicious", "とてもおいしいです", "This is delicious"),
    ]),
    ("travel", "移動", "Getting around", [
        ("station", "駅はどこですか？", "Where is the station?"),
        ("toilet", "トイレはどこですか？", "Where is the toilet?"),
        ("fare", "運賃はいくらですか？", "How much is the fare?"),
        ("airportbus", "このバスは空港に行きますか？", "Does this bus go to the airport?"),
        ("address", "この住所までお願いします", "Please take me to this address"),
        ("stophere", "ここで止めてください", "Please stop here"),
    ]),
    ("shop", "買い物", "Shopping", [
        ("howmuch", "これはいくらですか？", "How much is this?"),
        ("othersize", "別のサイズはありますか？", "Do you have this in another size?"),
        ("card", "クレジットカードは使えますか？", "Can I pay by credit card?"),
        ("takethis", "これをください", "I'll take this one"),
        ("receipt", "レシートをください", "Could I have a receipt, please?"),
        ("lookingonly", "見ているだけです", "I'm just looking, thank you"),
    ]),
    ("hotel", "宿泊", "Hotel", [
        ("reservation", "予約しています", "I have a reservation"),
        ("checkin", "チェックインをお願いします", "I'd like to check in, please"),
        ("checkout", "チェックアウトは何時ですか？", "What time is check-out?"),
        ("breakfast", "朝食は付いていますか？", "Is breakfast included?"),
        ("wifi", "Wi-Fiは使えますか？", "Is there Wi-Fi?"),
        ("taxi", "タクシーを呼んでください", "Could you call a taxi, please?"),
    ]),
    ("emergency", "緊急・体調", "Emergency", [
        ("help", "助けてください！", "Help!"),
        ("ambulance", "救急車を呼んでください", "Please call an ambulance"),
        ("police", "警察を呼んでください", "Please call the police"),
        ("doctor", "医者が必要です", "I need a doctor"),
        ("passport", "パスポートをなくしました", "I've lost my passport"),
        ("sick", "気分が悪いです", "I feel sick"),
    ]),
]

# 言語コード(BCP-47, languages.py の code) -> {フレーズID: 訳}。順番は上の CATEGORIES と同じ
T = {}

T["ja-JP"] = {p[0]: p[1] for c in CATEGORIES for p in c[3]}
T["en-US"] = {p[0]: p[2] for c in CATEGORIES for p in c[3]}

def _add(code, lines):
    ids = [p[0] for c in CATEGORIES for p in c[3]]
    lines = [l.strip() for l in lines.strip().split("\n")]
    assert len(lines) == len(ids), (code, len(lines), len(ids))
    T[code] = dict(zip(ids, lines))

_add("zh-CN", """
你好
非常感谢
打扰一下
对不起
我听不懂
请您说慢一点
请给我们两位的位子
请给我看一下菜单
您有什么推荐的？
我对花生过敏
请结账
这个很好吃
车站在哪里？
洗手间在哪里？
车费是多少？
这辆公交车去机场吗？
请送我到这个地址
请在这里停车
这个多少钱？
这个有其他尺码吗？
可以用信用卡付款吗？
我要这个
请给我收据
我只是随便看看，谢谢
我已经预订了
我想办理入住
几点退房？
含早餐吗？
有无线网络（Wi-Fi）吗？
请帮我叫一辆出租车
救命！
请叫救护车
请报警
我需要看医生
我的护照丢了
我觉得不舒服
""")

_add("zh-TW", """
你好
非常謝謝您
不好意思（請問一下）
對不起
我聽不懂
請您說慢一點
請給我兩位的座位
請給我看一下菜單
您有什麼推薦的嗎？
我對花生過敏
麻煩結帳
這個很好吃
車站在哪裡？
洗手間在哪裡？
車資多少錢？
這班公車有到機場嗎？
請載我到這個地址
請在這裡停車
這個多少錢？
這個有其他尺寸嗎？
可以刷信用卡嗎？
我要這個
請給我收據
我只是看看，謝謝
我有預約
我想辦理入住
幾點退房？
有含早餐嗎？
有無線網路（Wi-Fi）嗎？
請幫我叫計程車
救命！
請叫救護車
請報警
我需要看醫生
我的護照遺失了
我覺得不舒服
""")

_add("ko-KR", """
안녕하세요
정말 감사합니다
실례합니다
죄송합니다
이해가 안 돼요
조금 더 천천히 말씀해 주시겠어요?
두 명이에요
메뉴판 좀 보여 주세요
추천 메뉴가 뭐예요?
저는 땅콩 알레르기가 있어요
계산해 주세요
정말 맛있어요
역이 어디예요?
화장실이 어디예요?
요금이 얼마예요?
이 버스는 공항에 가나요?
이 주소로 가 주세요
여기서 세워 주세요
이거 얼마예요?
다른 사이즈 있어요?
신용카드로 결제할 수 있나요?
이걸로 할게요
영수증 주세요
그냥 구경하는 거예요, 감사합니다
예약했어요
체크인하고 싶어요
체크아웃은 몇 시예요?
조식이 포함돼 있나요?
와이파이 되나요?
택시 좀 불러 주시겠어요?
도와주세요!
구급차를 불러 주세요
경찰을 불러 주세요
의사가 필요해요
여권을 잃어버렸어요
몸이 안 좋아요
""")

_add("es-ES", """
Hola
Muchas gracias
Disculpe
Lo siento
No entiendo
¿Podría hablar más despacio, por favor?
Una mesa para dos, por favor
¿Me trae la carta, por favor?
¿Qué me recomienda?
Soy alérgico/a a los cacahuetes
La cuenta, por favor
Está muy rico
¿Dónde está la estación?
¿Dónde está el baño?
¿Cuánto cuesta el billete?
¿Este autobús va al aeropuerto?
Lléveme a esta dirección, por favor
Pare aquí, por favor
¿Cuánto cuesta esto?
¿Lo tiene en otra talla?
¿Puedo pagar con tarjeta de crédito?
Me llevo este
¿Me da el recibo, por favor?
Solo estoy mirando, gracias
Tengo una reserva
Quisiera hacer el registro de entrada, por favor
¿A qué hora es la salida?
¿El desayuno está incluido?
¿Hay wifi?
¿Podría llamarme un taxi, por favor?
¡Ayuda!
Llame a una ambulancia, por favor
Llame a la policía, por favor
Necesito un médico
He perdido mi pasaporte
Me siento mal
""")

_add("fr-FR", """
Bonjour
Merci beaucoup
Excusez-moi
Désolé(e)
Je ne comprends pas
Pourriez-vous parler plus lentement, s'il vous plaît ?
Une table pour deux, s'il vous plaît
Pouvez-vous m'apporter la carte, s'il vous plaît ?
Que me recommandez-vous ?
Je suis allergique aux cacahuètes
L'addition, s'il vous plaît
C'est délicieux
Où est la gare ?
Où sont les toilettes ?
Combien coûte le billet ?
Ce bus va-t-il à l'aéroport ?
Emmenez-moi à cette adresse, s'il vous plaît
Arrêtez-vous ici, s'il vous plaît
Combien ça coûte ?
Avez-vous cela dans une autre taille ?
Puis-je payer par carte bancaire ?
Je prends celui-ci
Puis-je avoir un reçu, s'il vous plaît ?
Je regarde seulement, merci
J'ai une réservation
Je voudrais m'enregistrer, s'il vous plaît
À quelle heure faut-il libérer la chambre ?
Le petit-déjeuner est-il compris ?
Y a-t-il du Wi-Fi ?
Pourriez-vous appeler un taxi, s'il vous plaît ?
Au secours !
Appelez une ambulance, s'il vous plaît
Appelez la police, s'il vous plaît
J'ai besoin d'un médecin
J'ai perdu mon passeport
Je me sens mal
""")

_add("de-DE", """
Hallo
Vielen Dank
Entschuldigung
Es tut mir leid
Ich verstehe nicht
Könnten Sie bitte langsamer sprechen?
Einen Tisch für zwei, bitte
Könnte ich bitte die Speisekarte sehen?
Was empfehlen Sie?
Ich bin allergisch gegen Erdnüsse
Die Rechnung, bitte
Das schmeckt köstlich
Wo ist der Bahnhof?
Wo ist die Toilette?
Wie viel kostet die Fahrkarte?
Fährt dieser Bus zum Flughafen?
Bitte bringen Sie mich zu dieser Adresse
Bitte halten Sie hier an
Wie viel kostet das?
Haben Sie das in einer anderen Größe?
Kann ich mit Kreditkarte bezahlen?
Ich nehme dieses
Könnte ich bitte eine Quittung haben?
Ich schaue nur, danke
Ich habe eine Reservierung
Ich möchte bitte einchecken
Um wie viel Uhr ist der Check-out?
Ist das Frühstück inbegriffen?
Gibt es WLAN?
Könnten Sie bitte ein Taxi rufen?
Hilfe!
Bitte rufen Sie einen Krankenwagen
Bitte rufen Sie die Polizei
Ich brauche einen Arzt
Ich habe meinen Reisepass verloren
Mir ist schlecht
""")

_add("it-IT", """
Ciao
Grazie mille
Mi scusi
Mi dispiace
Non capisco
Potrebbe parlare più lentamente, per favore?
Un tavolo per due, per favore
Posso vedere il menù, per favore?
Che cosa mi consiglia?
Sono allergico/a alle arachidi
Il conto, per favore
È buonissimo
Dov'è la stazione?
Dov'è il bagno?
Quanto costa il biglietto?
Questo autobus va all'aeroporto?
Mi porti a questo indirizzo, per favore
Si fermi qui, per favore
Quanto costa questo?
Ce l'avete in un'altra taglia?
Posso pagare con la carta di credito?
Prendo questo
Posso avere la ricevuta, per favore?
Sto solo guardando, grazie
Ho una prenotazione
Vorrei fare il check-in, per favore
A che ora si deve lasciare la camera?
La colazione è inclusa?
C'è il Wi-Fi?
Potrebbe chiamare un taxi, per favore?
Aiuto!
Chiami un'ambulanza, per favore
Chiami la polizia, per favore
Ho bisogno di un medico
Ho perso il passaporto
Mi sento male
""")

_add("pt-BR", """
Olá
Muito obrigado
Com licença
Desculpe
Não entendo
Pode falar mais devagar, por favor?
Uma mesa para duas pessoas, por favor
Pode me mostrar o cardápio, por favor?
O que você recomenda?
Sou alérgico a amendoim
A conta, por favor
Está delicioso
Onde fica a estação?
Onde fica o banheiro?
Quanto custa a passagem?
Este ônibus vai para o aeroporto?
Por favor, me leve a este endereço
Pare aqui, por favor
Quanto custa isto?
Você tem em outro tamanho?
Posso pagar com cartão de crédito?
Vou levar este
Pode me dar o recibo, por favor?
Estou só olhando, obrigado
Tenho uma reserva
Gostaria de fazer o check-in, por favor
A que horas é o check-out?
O café da manhã está incluído?
Tem Wi-Fi?
Pode chamar um táxi, por favor?
Socorro!
Por favor, chame uma ambulância
Por favor, chame a polícia
Preciso de um médico
Perdi meu passaporte
Estou me sentindo mal
""")

_add("ru-RU", """
Здравствуйте
Большое спасибо
Извините
Простите
Я не понимаю
Говорите, пожалуйста, помедленнее
Столик на двоих, пожалуйста
Можно посмотреть меню?
Что вы порекомендуете?
У меня аллергия на арахис
Счёт, пожалуйста
Очень вкусно
Где находится вокзал?
Где туалет?
Сколько стоит проезд?
Этот автобус идёт в аэропорт?
Отвезите меня по этому адресу, пожалуйста
Остановитесь здесь, пожалуйста
Сколько это стоит?
Есть другой размер?
Можно оплатить кредитной картой?
Я возьму это
Можно чек, пожалуйста?
Я просто смотрю, спасибо
У меня забронирован номер
Я хотел бы заселиться
Во сколько нужно освободить номер?
Завтрак включён?
Есть Wi-Fi?
Вызовите, пожалуйста, такси
Помогите!
Вызовите скорую помощь, пожалуйста
Вызовите полицию, пожалуйста
Мне нужен врач
Я потерял паспорт
Мне плохо
""")

_add("th-TH", """
สวัสดี
ขอบคุณมาก
ขอโทษนะคะ/ครับ
ขอโทษ
ไม่เข้าใจ
ช่วยพูดช้าลงหน่อยได้ไหม
ขอโต๊ะสำหรับสองคน
ขอดูเมนูหน่อย
มีอะไรแนะนำไหม
ฉันแพ้ถั่วลิสง
เช็คบิลด้วย
อร่อยมาก
สถานีอยู่ที่ไหน
ห้องน้ำอยู่ที่ไหน
ค่าโดยสารเท่าไร
รถบัสคันนี้ไปสนามบินไหม
ช่วยไปส่งที่ที่อยู่นี้หน่อย
จอดตรงนี้
อันนี้ราคาเท่าไร
มีไซซ์อื่นไหม
จ่ายด้วยบัตรเครดิตได้ไหม
เอาอันนี้
ขอใบเสร็จด้วย
ขอดูเฉย ๆ ค่ะ/ครับ ขอบคุณ
ฉันจองไว้แล้ว
ขอเช็คอิน
เช็คเอาท์กี่โมง
รวมอาหารเช้าไหม
มี Wi-Fi ไหม
ช่วยเรียกแท็กซี่ให้หน่อยได้ไหม
ช่วยด้วย!
ช่วยเรียกรถพยาบาลหน่อย
ช่วยเรียกตำรวจหน่อย
ฉันต้องการหมอ
ฉันทำหนังสือเดินทางหาย
ฉันรู้สึกไม่สบาย
""")

_add("vi-VN", """
Xin chào
Cảm ơn rất nhiều
Xin lỗi
Tôi xin lỗi
Tôi không hiểu
Bạn có thể nói chậm hơn được không?
Cho tôi một bàn cho hai người
Cho tôi xem thực đơn được không?
Bạn gợi ý món nào?
Tôi bị dị ứng đậu phộng
Tính tiền giúp tôi
Món này ngon quá
Nhà ga ở đâu?
Nhà vệ sinh ở đâu?
Giá vé là bao nhiêu?
Xe buýt này có đi sân bay không?
Làm ơn đưa tôi đến địa chỉ này
Làm ơn dừng ở đây
Cái này giá bao nhiêu?
Cái này có cỡ khác không?
Tôi có thể trả bằng thẻ tín dụng không?
Tôi lấy cái này
Cho tôi xin hóa đơn
Tôi chỉ xem thôi, cảm ơn
Tôi đã đặt phòng
Tôi muốn nhận phòng
Mấy giờ phải trả phòng?
Có bao gồm bữa sáng không?
Có Wi-Fi không?
Bạn có thể gọi giúp tôi một chiếc taxi không?
Cứu tôi với!
Làm ơn gọi xe cấp cứu
Làm ơn gọi cảnh sát
Tôi cần gặp bác sĩ
Tôi bị mất hộ chiếu
Tôi cảm thấy không khỏe
""")

_add("id-ID", """
Halo
Terima kasih banyak
Permisi
Maaf
Saya tidak mengerti
Bisakah Anda bicara lebih pelan?
Meja untuk dua orang, tolong
Boleh saya lihat menunya?
Apa yang Anda rekomendasikan?
Saya alergi kacang tanah
Tolong bonnya
Ini enak sekali
Di mana stasiunnya?
Di mana toiletnya?
Berapa tarifnya?
Apakah bus ini menuju bandara?
Tolong antar saya ke alamat ini
Tolong berhenti di sini
Berapa harga ini?
Apakah ada ukuran lain?
Bisakah saya membayar dengan kartu kredit?
Saya ambil yang ini
Boleh minta struknya?
Saya hanya melihat-lihat, terima kasih
Saya sudah memesan kamar
Saya ingin check-in
Jam berapa check-out?
Apakah sudah termasuk sarapan?
Apakah ada Wi-Fi?
Bisakah Anda memanggilkan taksi?
Tolong!
Tolong panggilkan ambulans
Tolong panggilkan polisi
Saya butuh dokter
Paspor saya hilang
Saya merasa tidak enak badan
""")

_add("ar-SA", """
مرحباً
شكراً جزيلاً
عفواً
أنا آسف
لا أفهم
هل يمكنك التحدث ببطء أكثر من فضلك؟
طاولة لشخصين من فضلك
هل يمكنني رؤية قائمة الطعام من فضلك؟
ماذا تنصحني أن آكل؟
لدي حساسية من الفول السوداني
الحساب من فضلك
هذا لذيذ جداً
أين المحطة؟
أين الحمّام؟
كم الأجرة؟
هل تذهب هذه الحافلة إلى المطار؟
من فضلك أوصلني إلى هذا العنوان
من فضلك توقف هنا
كم سعر هذا؟
هل لديكم مقاس آخر؟
هل يمكنني الدفع ببطاقة الائتمان؟
سآخذ هذا
هل يمكنني الحصول على الإيصال من فضلك؟
أنا أتفرج فقط، شكراً
لدي حجز
أودّ تسجيل الوصول من فضلك
متى موعد المغادرة؟
هل الإفطار مشمول؟
هل يوجد واي فاي؟
هل يمكنك استدعاء سيارة أجرة من فضلك؟
النجدة!
من فضلك اتصل بالإسعاف
من فضلك اتصل بالشرطة
أحتاج إلى طبيب
فقدت جواز سفري
أشعر بتوعّك
""")

_add("hi-IN", """
नमस्ते
बहुत धन्यवाद
माफ़ कीजिए
मुझे खेद है
मुझे समझ नहीं आया
कृपया थोड़ा धीरे बोलिए
दो लोगों के लिए एक मेज़ चाहिए
क्या मैं मेन्यू देख सकता हूँ?
आप क्या सुझाव देंगे?
मुझे मूँगफली से एलर्जी है
कृपया बिल दीजिए
यह बहुत स्वादिष्ट है
स्टेशन कहाँ है?
शौचालय कहाँ है?
किराया कितना है?
क्या यह बस हवाई अड्डे जाती है?
कृपया मुझे इस पते पर ले चलिए
कृपया यहीं रोक दीजिए
यह कितने का है?
क्या यह दूसरे साइज़ में है?
क्या मैं क्रेडिट कार्ड से भुगतान कर सकता हूँ?
मैं यह लूँगा
कृपया रसीद दीजिए
मैं बस देख रहा हूँ, धन्यवाद
मेरी बुकिंग है
मैं चेक-इन करना चाहता हूँ
चेक-आउट कितने बजे है?
क्या नाश्ता शामिल है?
क्या वाई-फ़ाई है?
क्या आप एक टैक्सी बुला सकते हैं?
बचाओ!
कृपया एम्बुलेंस बुलाइए
कृपया पुलिस को बुलाइए
मुझे डॉक्टर चाहिए
मेरा पासपोर्ट खो गया है
मेरी तबीयत ठीक नहीं है
""")

_add("tr-TR", """
Merhaba
Çok teşekkür ederim
Affedersiniz
Özür dilerim
Anlamıyorum
Lütfen biraz daha yavaş konuşur musunuz?
İki kişilik bir masa lütfen
Menüyü görebilir miyim lütfen?
Ne tavsiye edersiniz?
Yer fıstığına alerjim var
Hesap lütfen
Çok lezzetli
İstasyon nerede?
Tuvalet nerede?
Ücret ne kadar?
Bu otobüs havalimanına gidiyor mu?
Lütfen beni bu adrese götürün
Lütfen burada durun
Bu ne kadar?
Bunun başka bir bedeni var mı?
Kredi kartıyla ödeyebilir miyim?
Bunu alıyorum
Fiş alabilir miyim lütfen?
Sadece bakıyorum, teşekkürler
Rezervasyonum var
Giriş yapmak istiyorum
Çıkış saati kaçta?
Kahvaltı dahil mi?
Wi-Fi var mı?
Lütfen bir taksi çağırır mısınız?
İmdat!
Lütfen ambulans çağırın
Lütfen polisi çağırın
Doktora ihtiyacım var
Pasaportumu kaybettim
Kendimi iyi hissetmiyorum
""")
