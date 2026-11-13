"""空港・飛行機で使えるフレーズ（固定文45個・5カテゴリ）。
人や場所の名前が入る文は入れず、そのまま使える文だけにしています。
phrasebook_data.py から読み込まれ、`python tools/build_phrasebook.py` で JSON に書き出されます。
※ 機械的な訳です。ネイティブの方に確認してもらうと安心です（このファイルか JSON を直して構いません）。"""

# (カテゴリID, 日本語名, 英語名, [(フレーズID, 日本語, 英語), ...])
AIRPORT_CATEGORIES = [
    ("ap_checkin", "空港：チェックイン・荷物", "Airport: check-in & bags", [
        ("ap_checkin_where", "チェックインカウンターはどこですか？", "Where is the check-in counter?"),
        ("ap_window", "窓側の席をお願いします", "I'd like a window seat, please"),
        ("ap_aisle", "通路側の席をお願いします", "I'd like an aisle seat, please"),
        ("ap_sit_together", "隣同士の席にしていただけますか？", "Could we sit together, please?"),
        ("ap_check_bag", "この荷物を預けたいです", "I'd like to check this bag"),
        ("ap_weight_limit", "荷物の重量制限は何キロですか？", "What is the baggage weight limit?"),
        ("ap_excess_fee", "超過料金はいくらですか？", "How much is the excess baggage fee?"),
        ("ap_carry_on", "これは機内に持ち込めますか？", "Can I take this on board as carry-on?"),
        ("ap_fragile", "割れ物が入っています。丁寧に扱ってください", "This bag has fragile items. Please handle it with care"),
    ]),
    ("ap_security", "保安検査・入国審査", "Security & immigration", [
        ("ap_security_where", "保安検査場はどこですか？", "Where is the security checkpoint?"),
        ("ap_liquids", "液体は持っていません", "I'm not carrying any liquids"),
        ("ap_laptop", "パソコンを出す必要がありますか？", "Do I need to take out my laptop?"),
        ("ap_sightseeing", "観光で来ました", "I'm here for sightseeing"),
        ("ap_stay_week", "1週間滞在します", "I'll be staying for one week"),
        ("ap_stay_hotel", "ホテルに滞在します", "I'll be staying at a hotel"),
        ("ap_return_ticket", "帰りの航空券があります", "I have a return ticket"),
        ("ap_declare_nothing", "申告するものはありません", "I have nothing to declare"),
        ("ap_first_visit", "初めての訪問です", "This is my first visit"),
    ]),
    ("ap_gate", "搭乗口・乗り継ぎ", "Gate & connections", [
        ("ap_gate_where", "搭乗口はどこですか？", "Where is the boarding gate?"),
        ("ap_boarding_time", "搭乗は何時からですか？", "What time does boarding start?"),
        ("ap_delayed", "このフライトは遅れていますか？", "Is this flight delayed?"),
        ("ap_gate_changed", "搭乗口は変更になりましたか？", "Has the gate been changed?"),
        ("ap_missed", "飛行機に乗り遅れました", "I missed my flight"),
        ("ap_next_flight", "次の便に変更できますか？", "Can I change to the next flight?"),
        ("ap_connecting", "乗り継ぎ便があります", "I have a connecting flight"),
        ("ap_transfer_desk", "乗り継ぎカウンターはどこですか？", "Where is the transfer desk?"),
        ("ap_wheelchair", "車椅子を手配していただけますか？", "Could you arrange a wheelchair for me?"),
    ]),
    ("ap_flight", "機内", "On the plane", [
        ("ap_my_seat", "私の席はどこですか？", "Where is my seat?"),
        ("ap_that_seat", "すみません、そこは私の席だと思います", "Excuse me, I think that's my seat"),
        ("ap_overhead", "荷物を上の棚に入れるのを手伝っていただけますか？", "Could you help me put my bag in the overhead bin?"),
        ("ap_get_past", "すみません、通していただけますか？", "Excuse me, may I get past?"),
        ("ap_restroom", "トイレに行きたいです", "I need to use the restroom"),
        ("ap_blanket", "毛布をいただけますか？", "Could I have a blanket, please?"),
        ("ap_water", "お水をいただけますか？", "Could I have some water, please?"),
        ("ap_veg_meal", "ベジタリアン向けの食事はありますか？", "Do you have a vegetarian meal?"),
        ("ap_motion_sick", "気分が悪いです。酔い止めはありますか？", "I feel sick. Do you have motion sickness medicine?"),
    ]),
    ("ap_arrival", "到着・荷物の受け取り", "Arrival & baggage claim", [
        ("ap_baggage_claim", "手荷物受取所はどこですか？", "Where is the baggage claim?"),
        ("ap_bag_missing", "荷物が出てきません", "My luggage hasn't come out"),
        ("ap_bag_damaged", "荷物が壊れています", "My luggage is damaged"),
        ("ap_lost_baggage", "紛失手荷物の窓口はどこですか？", "Where is the lost baggage counter?"),
        ("ap_exchange", "両替所はどこですか？", "Where can I exchange money?"),
        ("ap_sim", "SIMカードはどこで買えますか？", "Where can I buy a SIM card?"),
        ("ap_taxi", "タクシー乗り場はどこですか？", "Where is the taxi stand?"),
        ("ap_train_city", "市内へ行く電車にはどこで乗れますか？", "Where can I take a train to the city center?"),
        ("ap_info_desk", "案内所はどこですか？", "Where is the information desk?"),
    ]),
]

AIRPORT_IDS = [p[0] for c in AIRPORT_CATEGORIES for p in c[3]]

# 言語コード -> 45行（AIRPORT_IDS と同じ順）
AIRPORT_TEXT = {}


def _add(code, lines):
    rows = [l.strip() for l in lines.strip().split("\n")]
    assert len(rows) == len(AIRPORT_IDS), (code, len(rows), len(AIRPORT_IDS))
    AIRPORT_TEXT[code] = dict(zip(AIRPORT_IDS, rows))


def add_all(T):
    """T[言語コード] に空港フレーズの訳を足す（ja-JP / en-US は CATEGORIES から作られる）"""
    for code, d in AIRPORT_TEXT.items():
        T[code].update(d)


_add("zh-CN", """
办理登机手续的柜台在哪里？
我想要靠窗的座位
我想要靠过道的座位
我们可以坐在一起吗？
我想托运这件行李
行李重量限制是多少公斤？
超重行李费是多少？
这个可以带上飞机吗？
行李里有易碎品，请小心搬运
安检口在哪里？
我没有携带任何液体
需要把电脑拿出来吗？
我是来旅游的
我会停留一周
我会住在酒店
我有回程机票
我没有需要申报的物品
这是我第一次来
登机口在哪里？
几点开始登机？
这个航班延误了吗？
登机口有变更吗？
我误了航班
可以改签到下一班吗？
我有转机航班
转机柜台在哪里？
可以帮我安排轮椅吗？
我的座位在哪里？
不好意思，这好像是我的座位
可以帮我把行李放进上方行李架吗？
不好意思，可以让我过一下吗？
我想去洗手间
可以给我一条毯子吗？
可以给我一杯水吗？
有素食餐吗？
我不舒服。有晕机药吗？
行李提取处在哪里？
我的行李没有出来
我的行李损坏了
行李遗失柜台在哪里？
哪里可以换钱？
哪里可以买到SIM卡？
出租车乘车处在哪里？
去市区的火车在哪里坐？
问询处在哪里？
""")

_add("zh-TW", """
報到櫃檯在哪裡？
我想要靠窗的座位
我想要靠走道的座位
我們可以坐在一起嗎？
我想託運這件行李
行李重量限制是幾公斤？
超重行李費是多少？
這個可以帶上飛機嗎？
行李裡有易碎品，請小心搬運
安檢口在哪裡？
我沒有攜帶任何液體
需要把電腦拿出來嗎？
我是來觀光的
我會停留一週
我會住在飯店
我有回程機票
我沒有需要申報的物品
這是我第一次來
登機門在哪裡？
幾點開始登機？
這個航班延誤了嗎？
登機門有變更嗎？
我錯過了航班
可以改到下一班嗎？
我有轉機航班
轉機櫃檯在哪裡？
可以幫我安排輪椅嗎？
我的座位在哪裡？
不好意思，這好像是我的座位
可以幫我把行李放進上方行李櫃嗎？
不好意思，可以讓我過一下嗎？
我想去洗手間
可以給我一條毯子嗎？
可以給我一杯水嗎？
有素食餐嗎？
我不舒服。有暈機藥嗎？
行李提領處在哪裡？
我的行李沒有出來
我的行李損壞了
遺失行李櫃檯在哪裡？
哪裡可以換錢？
哪裡可以買到SIM卡？
計程車乘車處在哪裡？
去市區的火車在哪裡搭？
服務台在哪裡？
""")

_add("ko-KR", """
체크인 카운터는 어디예요?
창가 쪽 자리로 부탁합니다
복도 쪽 자리로 부탁합니다
같이 앉을 수 있을까요?
이 짐을 부치고 싶어요
수하물 무게 제한은 몇 킬로예요?
초과 수하물 요금은 얼마예요?
이건 기내에 가지고 탈 수 있나요?
깨지기 쉬운 물건이 들어 있어요. 조심히 다뤄 주세요
보안 검색대는 어디예요?
액체는 가지고 있지 않아요
노트북을 꺼내야 하나요?
관광하러 왔어요
일주일 동안 머물 거예요
호텔에 머물 거예요
돌아가는 항공권이 있어요
신고할 물건이 없어요
처음 방문하는 거예요
탑승구는 어디예요?
탑승은 몇 시부터예요?
이 항공편은 지연되고 있나요?
탑승구가 바뀌었나요?
비행기를 놓쳤어요
다음 항공편으로 변경할 수 있나요?
연결 항공편이 있어요
환승 카운터는 어디예요?
휠체어를 준비해 주실 수 있나요?
제 좌석은 어디예요?
실례합니다, 거기는 제 자리인 것 같아요
짐을 위쪽 선반에 넣는 것 좀 도와주시겠어요?
실례합니다, 좀 지나가도 될까요?
화장실에 가고 싶어요
담요를 주시겠어요?
물 좀 주시겠어요?
채식 기내식이 있나요?
속이 안 좋아요. 멀미약 있나요?
수하물 찾는 곳은 어디예요?
제 짐이 나오지 않아요
제 짐이 파손됐어요
분실 수하물 카운터는 어디예요?
환전소는 어디예요?
SIM 카드는 어디서 살 수 있나요?
택시 승차장은 어디예요?
시내로 가는 기차는 어디서 탈 수 있나요?
안내 데스크는 어디예요?
""")

_add("es-ES", """
¿Dónde está el mostrador de facturación?
Quisiera un asiento de ventanilla, por favor
Quisiera un asiento de pasillo, por favor
¿Podemos sentarnos juntos, por favor?
Quisiera facturar esta maleta
¿Cuál es el límite de peso del equipaje?
¿Cuánto cuesta el exceso de equipaje?
¿Puedo llevar esto en cabina?
Esta maleta contiene objetos frágiles. Trátela con cuidado
¿Dónde está el control de seguridad?
No llevo ningún líquido
¿Tengo que sacar el portátil?
He venido de turismo
Me quedaré una semana
Me alojaré en un hotel
Tengo billete de vuelta
No tengo nada que declarar
Es mi primera visita
¿Dónde está la puerta de embarque?
¿A qué hora empieza el embarque?
¿Este vuelo lleva retraso?
¿Ha cambiado la puerta de embarque?
He perdido mi vuelo
¿Puedo cambiar al siguiente vuelo?
Tengo un vuelo de conexión
¿Dónde está el mostrador de transferencias?
¿Podría conseguirme una silla de ruedas?
¿Dónde está mi asiento?
Disculpe, creo que ese es mi asiento
¿Podría ayudarme a guardar la maleta en el compartimento superior?
Disculpe, ¿me deja pasar?
Necesito ir al baño
¿Me podría dar una manta, por favor?
¿Me podría dar un poco de agua, por favor?
¿Tienen menú vegetariano?
Me siento mal. ¿Tienen medicamento para el mareo?
¿Dónde está la recogida de equipajes?
Mi equipaje no ha salido
Mi equipaje está dañado
¿Dónde está el mostrador de equipajes perdidos?
¿Dónde puedo cambiar dinero?
¿Dónde puedo comprar una tarjeta SIM?
¿Dónde está la parada de taxis?
¿Dónde puedo tomar un tren al centro de la ciudad?
¿Dónde está el punto de información?
""")

_add("fr-FR", """
Où est le comptoir d'enregistrement ?
Je voudrais une place côté hublot, s'il vous plaît
Je voudrais une place côté couloir, s'il vous plaît
Pouvons-nous être assis ensemble, s'il vous plaît ?
Je voudrais enregistrer ce bagage
Quelle est la limite de poids des bagages ?
Combien coûte l'excédent de bagages ?
Puis-je emporter ceci en cabine ?
Ce bagage contient des objets fragiles. Faites attention, s'il vous plaît
Où est le contrôle de sécurité ?
Je n'ai aucun liquide
Dois-je sortir mon ordinateur portable ?
Je suis venu en touriste
Je resterai une semaine
Je séjournerai à l'hôtel
J'ai un billet retour
Je n'ai rien à déclarer
C'est ma première visite
Où est la porte d'embarquement ?
À quelle heure commence l'embarquement ?
Ce vol est-il retardé ?
La porte d'embarquement a-t-elle changé ?
J'ai raté mon vol
Puis-je prendre le prochain vol ?
J'ai un vol de correspondance
Où est le comptoir des correspondances ?
Pourriez-vous me procurer un fauteuil roulant ?
Où est ma place ?
Excusez-moi, je crois que c'est ma place
Pourriez-vous m'aider à mettre mon bagage dans le compartiment au-dessus ?
Excusez-moi, puis-je passer ?
J'ai besoin d'aller aux toilettes
Pourrais-je avoir une couverture, s'il vous plaît ?
Pourrais-je avoir de l'eau, s'il vous plaît ?
Avez-vous un repas végétarien ?
Je me sens mal. Avez-vous un médicament contre le mal des transports ?
Où est la livraison des bagages ?
Mon bagage n'est pas sorti
Mon bagage est endommagé
Où est le guichet des bagages perdus ?
Où puis-je changer de l'argent ?
Où puis-je acheter une carte SIM ?
Où est la station de taxis ?
Où puis-je prendre un train pour le centre-ville ?
Où est le comptoir d'information ?
""")

_add("de-DE", """
Wo ist der Check-in-Schalter?
Ich hätte gern einen Fensterplatz
Ich hätte gern einen Gangplatz
Können wir nebeneinandersitzen?
Ich möchte diese Tasche aufgeben
Wie hoch ist die Gepäckgewichtsgrenze?
Wie viel kostet das Übergepäck?
Kann ich das als Handgepäck mitnehmen?
In dieser Tasche sind zerbrechliche Gegenstände. Bitte vorsichtig behandeln
Wo ist die Sicherheitskontrolle?
Ich habe keine Flüssigkeiten dabei
Muss ich meinen Laptop herausnehmen?
Ich bin als Tourist hier
Ich bleibe eine Woche
Ich übernachte in einem Hotel
Ich habe ein Rückflugticket
Ich habe nichts zu verzollen
Das ist mein erster Besuch
Wo ist das Gate?
Wann beginnt das Boarding?
Hat dieser Flug Verspätung?
Wurde das Gate geändert?
Ich habe meinen Flug verpasst
Kann ich auf den nächsten Flug umbuchen?
Ich habe einen Anschlussflug
Wo ist der Transferschalter?
Könnten Sie einen Rollstuhl für mich organisieren?
Wo ist mein Platz?
Entschuldigung, ich glaube, das ist mein Platz
Könnten Sie mir helfen, meine Tasche im Gepäckfach zu verstauen?
Entschuldigung, darf ich durch?
Ich muss auf die Toilette
Könnte ich bitte eine Decke haben?
Könnte ich bitte etwas Wasser haben?
Haben Sie ein vegetarisches Menü?
Mir ist schlecht. Haben Sie ein Mittel gegen Reiseübelkeit?
Wo ist die Gepäckausgabe?
Mein Gepäck ist nicht angekommen
Mein Gepäck ist beschädigt
Wo ist der Schalter für verlorenes Gepäck?
Wo kann ich Geld wechseln?
Wo kann ich eine SIM-Karte kaufen?
Wo ist der Taxistand?
Wo kann ich einen Zug ins Stadtzentrum nehmen?
Wo ist die Information?
""")

_add("it-IT", """
Dov'è il banco del check-in?
Vorrei un posto vicino al finestrino, per favore
Vorrei un posto lato corridoio, per favore
Possiamo sederci vicini, per favore?
Vorrei imbarcare questa valigia
Qual è il limite di peso del bagaglio?
Quanto costa l'eccesso di bagaglio?
Posso portarlo a bordo come bagaglio a mano?
Questa valigia contiene oggetti fragili. La maneggi con cura
Dov'è il controllo di sicurezza?
Non ho liquidi con me
Devo tirare fuori il portatile?
Sono qui per turismo
Resterò una settimana
Alloggerò in un hotel
Ho il biglietto di ritorno
Non ho niente da dichiarare
È la mia prima visita
Dov'è il gate d'imbarco?
A che ora inizia l'imbarco?
Questo volo è in ritardo?
Il gate è cambiato?
Ho perso il volo
Posso cambiare con il prossimo volo?
Ho un volo in coincidenza
Dov'è il banco dei transiti?
Potrebbe organizzarmi una sedia a rotelle?
Dov'è il mio posto?
Mi scusi, credo che quello sia il mio posto
Potrebbe aiutarmi a mettere la valigia nella cappelliera?
Mi scusi, posso passare?
Ho bisogno di andare in bagno
Potrei avere una coperta, per favore?
Potrei avere dell'acqua, per favore?
Avete un pasto vegetariano?
Mi sento male. Avete un farmaco per il mal d'aria?
Dov'è il ritiro bagagli?
Il mio bagaglio non è uscito
Il mio bagaglio è danneggiato
Dov'è lo sportello bagagli smarriti?
Dove posso cambiare i soldi?
Dove posso comprare una scheda SIM?
Dov'è la fermata dei taxi?
Dove posso prendere un treno per il centro città?
Dov'è il punto informazioni?
""")

_add("pt-BR", """
Onde fica o balcão de check-in?
Eu gostaria de um assento na janela, por favor
Eu gostaria de um assento no corredor, por favor
Podemos sentar juntos, por favor?
Eu gostaria de despachar esta mala
Qual é o limite de peso da bagagem?
Quanto custa o excesso de bagagem?
Posso levar isto na cabine?
Esta mala tem itens frágeis. Por favor, manuseie com cuidado
Onde fica a inspeção de segurança?
Não estou levando nenhum líquido
Preciso tirar o notebook?
Vim a passeio
Vou ficar uma semana
Vou ficar em um hotel
Tenho passagem de volta
Não tenho nada a declarar
É a minha primeira visita
Onde fica o portão de embarque?
A que horas começa o embarque?
Este voo está atrasado?
O portão de embarque mudou?
Perdi meu voo
Posso trocar para o próximo voo?
Tenho um voo de conexão
Onde fica o balcão de conexões?
Você poderia providenciar uma cadeira de rodas?
Onde fica o meu assento?
Com licença, acho que esse é o meu assento
Você poderia me ajudar a colocar a mala no compartimento superior?
Com licença, posso passar?
Preciso ir ao banheiro
Poderia me dar um cobertor, por favor?
Poderia me dar um copo de água, por favor?
Vocês têm refeição vegetariana?
Estou me sentindo mal. Vocês têm remédio para enjoo?
Onde fica a esteira de bagagens?
Minha bagagem não saiu
Minha bagagem está danificada
Onde fica o balcão de bagagens extraviadas?
Onde posso trocar dinheiro?
Onde posso comprar um chip SIM?
Onde fica o ponto de táxi?
Onde posso pegar um trem para o centro da cidade?
Onde fica o balcão de informações?
""")

_add("ru-RU", """
Где стойка регистрации?
Мне, пожалуйста, место у окна
Мне, пожалуйста, место у прохода
Можно нам сесть рядом, пожалуйста?
Я хочу сдать этот багаж
Каково ограничение по весу багажа?
Сколько стоит перевес багажа?
Можно взять это с собой в салон?
В сумке хрупкие вещи. Пожалуйста, обращайтесь осторожно
Где пункт досмотра?
У меня нет жидкостей
Нужно ли доставать ноутбук?
Я приехал как турист
Я пробуду одну неделю
Я остановлюсь в отеле
У меня есть обратный билет
Мне нечего декларировать
Я здесь впервые
Где выход на посадку?
Во сколько начинается посадка?
Этот рейс задерживается?
Выход на посадку изменили?
Я опоздал на рейс
Можно перейти на следующий рейс?
У меня стыковочный рейс
Где стойка трансфера?
Не могли бы вы организовать для меня инвалидную коляску?
Где моё место?
Извините, кажется, это моё место
Не могли бы вы помочь мне положить сумку на верхнюю полку?
Извините, можно пройти?
Мне нужно в туалет
Можно мне плед, пожалуйста?
Можно мне воды, пожалуйста?
У вас есть вегетарианское питание?
Мне плохо. У вас есть лекарство от укачивания?
Где выдача багажа?
Мой багаж не вышел
Мой багаж повреждён
Где стойка розыска утерянного багажа?
Где можно обменять деньги?
Где можно купить SIM-карту?
Где стоянка такси?
Где можно сесть на поезд до центра города?
Где справочная?
""")

_add("th-TH", """
เคาน์เตอร์เช็กอินอยู่ที่ไหน
ขอที่นั่งริมหน้าต่าง
ขอที่นั่งริมทางเดิน
ขอนั่งติดกันได้ไหม
ฉันต้องการเช็กอินกระเป๋าใบนี้
น้ำหนักกระเป๋าสูงสุดกี่กิโลกรัม
ค่าน้ำหนักเกินเท่าไร
ของนี้นำขึ้นเครื่องได้ไหม
ในกระเป๋ามีของแตกง่าย กรุณาระวังด้วย
จุดตรวจความปลอดภัยอยู่ที่ไหน
ฉันไม่ได้นำของเหลวมา
ต้องเอาแล็ปท็อปออกไหม
ฉันมาท่องเที่ยว
ฉันจะพักหนึ่งสัปดาห์
ฉันจะพักที่โรงแรม
ฉันมีตั๋วขากลับ
ฉันไม่มีของต้องสำแดง
นี่เป็นการมาเยือนครั้งแรกของฉัน
ประตูขึ้นเครื่องอยู่ที่ไหน
เริ่มขึ้นเครื่องกี่โมง
เที่ยวบินนี้ล่าช้าไหม
เปลี่ยนประตูขึ้นเครื่องหรือเปล่า
ฉันตกเครื่อง
เปลี่ยนเป็นเที่ยวบินถัดไปได้ไหม
ฉันมีเที่ยวบินต่อเครื่อง
เคาน์เตอร์ต่อเครื่องอยู่ที่ไหน
ช่วยจัดเตรียมรถเข็นให้ได้ไหม
ที่นั่งของฉันอยู่ที่ไหน
ขอโทษ ฉันคิดว่านั่นเป็นที่นั่งของฉัน
ช่วยยกกระเป๋าใส่ช่องเก็บของด้านบนให้หน่อยได้ไหม
ขอโทษ ขอผ่านหน่อยได้ไหม
ฉันอยากไปห้องน้ำ
ขอผ้าห่มหน่อยได้ไหม
ขอน้ำหน่อยได้ไหม
มีอาหารมังสวิรัติไหม
ฉันรู้สึกไม่สบาย มียาแก้เมาเครื่องบินไหม
จุดรับกระเป๋าอยู่ที่ไหน
กระเป๋าของฉันยังไม่ออกมา
กระเป๋าของฉันเสียหาย
เคาน์เตอร์กระเป๋าสูญหายอยู่ที่ไหน
แลกเงินได้ที่ไหน
ซื้อซิมการ์ดได้ที่ไหน
จุดขึ้นแท็กซี่อยู่ที่ไหน
นั่งรถไฟเข้าตัวเมืองได้ที่ไหน
ศูนย์ข้อมูลอยู่ที่ไหน
""")

_add("vi-VN", """
Quầy làm thủ tục ở đâu?
Tôi muốn ngồi cạnh cửa sổ
Tôi muốn ngồi cạnh lối đi
Chúng tôi có thể ngồi cạnh nhau không?
Tôi muốn ký gửi hành lý này
Giới hạn trọng lượng hành lý là bao nhiêu?
Phí quá cân là bao nhiêu?
Tôi có thể mang cái này lên máy bay không?
Trong túi có đồ dễ vỡ. Xin hãy cẩn thận
Khu vực kiểm tra an ninh ở đâu?
Tôi không mang theo chất lỏng
Tôi có cần lấy máy tính xách tay ra không?
Tôi đến để du lịch
Tôi sẽ ở một tuần
Tôi sẽ ở khách sạn
Tôi có vé khứ hồi
Tôi không có gì cần khai báo
Đây là lần đầu tiên tôi đến
Cổng lên máy bay ở đâu?
Mấy giờ bắt đầu lên máy bay?
Chuyến bay này có bị trễ không?
Cổng lên máy bay có thay đổi không?
Tôi bị lỡ chuyến bay
Tôi có thể đổi sang chuyến bay tiếp theo không?
Tôi có chuyến bay nối chuyến
Quầy nối chuyến ở đâu?
Bạn có thể sắp xếp xe lăn giúp tôi không?
Ghế của tôi ở đâu?
Xin lỗi, tôi nghĩ đó là ghế của tôi
Bạn có thể giúp tôi để hành lý lên ngăn trên không?
Xin lỗi, cho tôi đi qua được không?
Tôi muốn đi vệ sinh
Cho tôi xin một cái chăn được không?
Cho tôi xin ít nước được không?
Có suất ăn chay không?
Tôi cảm thấy không khỏe. Có thuốc chống say không?
Nơi nhận hành lý ở đâu?
Hành lý của tôi chưa ra
Hành lý của tôi bị hỏng
Quầy hành lý thất lạc ở đâu?
Tôi có thể đổi tiền ở đâu?
Tôi có thể mua SIM ở đâu?
Điểm đón taxi ở đâu?
Tôi có thể đi tàu vào trung tâm thành phố ở đâu?
Quầy thông tin ở đâu?
""")

_add("id-ID", """
Di mana konter check-in?
Saya mau kursi dekat jendela
Saya mau kursi dekat lorong
Bisakah kami duduk berdekatan?
Saya mau mendaftarkan tas ini ke bagasi
Berapa batas berat bagasi?
Berapa biaya kelebihan bagasi?
Bolehkah ini dibawa ke kabin?
Di dalam tas ada barang pecah belah. Mohon ditangani dengan hati-hati
Di mana pemeriksaan keamanan?
Saya tidak membawa cairan
Apakah saya harus mengeluarkan laptop?
Saya datang untuk berwisata
Saya akan tinggal selama seminggu
Saya akan menginap di hotel
Saya punya tiket pulang
Saya tidak punya barang yang perlu dilaporkan
Ini kunjungan pertama saya
Di mana gerbang keberangkatan?
Pukul berapa boarding dimulai?
Apakah penerbangan ini tertunda?
Apakah gerbangnya berubah?
Saya ketinggalan pesawat
Bisakah saya pindah ke penerbangan berikutnya?
Saya punya penerbangan lanjutan
Di mana konter transfer?
Bisakah Anda menyiapkan kursi roda untuk saya?
Di mana kursi saya?
Permisi, sepertinya itu kursi saya
Bisakah Anda membantu saya menaruh tas di kabin atas?
Permisi, boleh saya lewat?
Saya mau ke toilet
Boleh minta selimut?
Boleh minta air putih?
Apakah ada makanan vegetarian?
Saya merasa mual. Apakah ada obat mabuk perjalanan?
Di mana pengambilan bagasi?
Bagasi saya belum keluar
Bagasi saya rusak
Di mana konter bagasi hilang?
Di mana saya bisa menukar uang?
Di mana saya bisa membeli kartu SIM?
Di mana pangkalan taksi?
Di mana saya bisa naik kereta ke pusat kota?
Di mana meja informasi?
""")

_add("ar-SA", """
أين مكتب تسجيل الوصول؟
أريد مقعدًا بجانب النافذة، من فضلك
أريد مقعدًا بجانب الممر، من فضلك
هل يمكننا الجلوس معًا، من فضلك؟
أريد شحن هذه الحقيبة
ما هو الحد الأقصى لوزن الأمتعة؟
كم رسوم الوزن الزائد؟
هل يمكنني حمل هذا معي إلى الطائرة؟
في الحقيبة أشياء قابلة للكسر. من فضلك تعامل معها بحذر
أين نقطة التفتيش الأمني؟
ليس معي أي سوائل
هل يجب أن أُخرج الحاسوب المحمول؟
جئت للسياحة
سأبقى لمدة أسبوع
سأقيم في فندق
لدي تذكرة عودة
ليس لدي شيء للتصريح عنه
هذه زيارتي الأولى
أين بوابة الصعود إلى الطائرة؟
متى يبدأ الصعود إلى الطائرة؟
هل هذه الرحلة متأخرة؟
هل تم تغيير البوابة؟
فاتتني رحلتي
هل يمكنني التغيير إلى الرحلة التالية؟
لدي رحلة ربط
أين مكتب الترانزيت؟
هل يمكنك ترتيب كرسي متحرك لي؟
أين مقعدي؟
المعذرة، أعتقد أن هذا مقعدي
هل يمكنك مساعدتي في وضع حقيبتي في الخزانة العلوية؟
المعذرة، هل يمكنني المرور؟
أريد الذهاب إلى دورة المياه
هل يمكنني الحصول على بطانية، من فضلك؟
هل يمكنني الحصول على ماء، من فضلك؟
هل لديكم وجبة نباتية؟
أشعر بالمرض. هل لديكم دواء لدوار الحركة؟
أين استلام الأمتعة؟
حقيبتي لم تخرج
حقيبتي تالفة
أين مكتب الأمتعة المفقودة؟
أين يمكنني صرف العملات؟
أين يمكنني شراء شريحة SIM؟
أين موقف سيارات الأجرة؟
من أين يمكنني ركوب القطار إلى وسط المدينة؟
أين مكتب الاستعلامات؟
""")

_add("hi-IN", """
चेक-इन काउंटर कहाँ है?
मुझे खिड़की वाली सीट चाहिए
मुझे गलियारे वाली सीट चाहिए
क्या हम साथ बैठ सकते हैं?
मुझे यह बैग चेक-इन कराना है
सामान के वज़न की सीमा कितनी है?
अतिरिक्त वज़न का शुल्क कितना है?
क्या मैं इसे केबिन में ले जा सकता हूँ?
बैग में नाज़ुक सामान है। कृपया सावधानी से संभालें
सुरक्षा जाँच कहाँ होती है?
मेरे पास कोई तरल पदार्थ नहीं है
क्या मुझे लैपटॉप बाहर निकालना होगा?
मैं यहाँ घूमने के लिए आया हूँ
मेरा ठहरना एक हफ़्ते का है
मेरा ठहरना होटल में है
मेरे पास वापसी का टिकट है
मेरे पास घोषित करने के लिए कुछ नहीं है
यह मेरी पहली यात्रा है
बोर्डिंग गेट कहाँ है?
बोर्डिंग कितने बजे शुरू होगी?
क्या यह उड़ान देरी से है?
क्या गेट बदल गया है?
मेरी उड़ान छूट गई
क्या मेरा टिकट अगली उड़ान में बदला जा सकता है?
मेरे पास कनेक्टिंग फ़्लाइट है
ट्रांसफ़र डेस्क कहाँ है?
क्या आप मेरे लिए व्हीलचेयर का इंतज़ाम कर सकते हैं?
मेरी सीट कहाँ है?
माफ़ कीजिए, मुझे लगता है यह मेरी सीट है
क्या आप मेरा बैग ऊपर वाले केबिन में रखने में मदद कर सकते हैं?
माफ़ कीजिए, ज़रा रास्ता देंगे?
मुझे शौचालय जाना है
क्या मुझे एक कंबल मिल सकता है?
क्या मुझे थोड़ा पानी मिल सकता है?
क्या आपके पास शाकाहारी भोजन है?
मेरी तबीयत ठीक नहीं है। क्या आपके पास मोशन सिकनेस की दवा है?
सामान लेने की जगह कहाँ है?
मेरा सामान नहीं आया
मेरा सामान क्षतिग्रस्त है
खोए हुए सामान का काउंटर कहाँ है?
करेंसी एक्सचेंज कहाँ है?
मुझे सिम कार्ड कहाँ मिलेगा?
टैक्सी स्टैंड कहाँ है?
शहर के केंद्र के लिए ट्रेन कहाँ से मिलेगी?
सूचना डेस्क कहाँ है?
""")

_add("tr-TR", """
Check-in kontuarı nerede?
Cam kenarı bir koltuk istiyorum, lütfen
Koridor tarafı bir koltuk istiyorum, lütfen
Birlikte oturabilir miyiz, lütfen?
Bu çantayı teslim etmek istiyorum
Bagaj ağırlık sınırı nedir?
Fazla bagaj ücreti ne kadar?
Bunu kabine alabilir miyim?
Çantada kırılgan eşyalar var. Lütfen dikkatli taşıyın
Güvenlik kontrolü nerede?
Yanımda sıvı yok
Dizüstü bilgisayarı çıkarmam gerekiyor mu?
Turistik amaçla geldim
Bir hafta kalacağım
Otelde kalacağım
Dönüş biletim var
Beyan edecek bir şeyim yok
Bu benim ilk ziyaretim
Biniş kapısı nerede?
Biniş saat kaçta başlıyor?
Bu uçuş rötarlı mı?
Kapı değişti mi?
Uçağımı kaçırdım
Bir sonraki uçuşa değiştirebilir miyim?
Aktarmalı bir uçuşum var
Transfer masası nerede?
Bana tekerlekli sandalye ayarlayabilir misiniz?
Koltuğum nerede?
Affedersiniz, sanırım orası benim koltuğum
Çantamı üstteki bölmeye koymama yardım eder misiniz?
Affedersiniz, geçebilir miyim?
Tuvalete gitmem gerekiyor
Bir battaniye alabilir miyim, lütfen?
Biraz su alabilir miyim, lütfen?
Vejetaryen menünüz var mı?
Kendimi kötü hissediyorum. Hareket tutması ilacınız var mı?
Bagaj teslim alanı nerede?
Bagajım çıkmadı
Bagajım hasar görmüş
Kayıp bagaj gişesi nerede?
Nerede para bozdurabilirim?
Nereden SIM kart alabilirim?
Taksi durağı nerede?
Şehir merkezine giden trene nereden binebilirim?
Danışma nerede?
""")
