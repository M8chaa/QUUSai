# # Testing the regex pattern with the provided text
# import re

# #월 유무 O (1,2 통과), 매일 무 X (3번), mbps 무 X (4번)
# regex_pattern1 = r"\[(.*?)\]\s*(.*?)\s*\|\s*([\d,]+원)\s*\|\s*(?:.*?월\s*([.\d]+(?:GB|MB)\+?))?.*?매일\s*([.\d]+(?:GB|MB)).*?\(([.\d]+(?:mbps|gbps))\).*?(무제한|\d+분).*?(무제한|\d+건).*?(LG U\+|SKT|KT).*?(LTE|3G|4G|5G)(?:.*?(\d+개월\s*이후\s*[\d,]+원))?"

# # 월+매일+mbps 일때 mbps 안나옴, 매일 + mbps X, 월 + mbps 일때 mbps 안나옴, 월 OK
# regex_pattern2 = r"\[(.*?)\]\s*(.*?)\s*\|\s*([\d,]+원)\s*\|\s*(?:.*?월\s*([.\d]+(?:GB|MB)))?(?:\s*\+\s*매일\s*([.\d]+(?:GB|MB)))?.*?(?:\(([.\d]+(?:mbps|gbps))\))?.*?(무제한|\d+분).*?(무제한|\d+건).*?(LG U\+|SKT|KT).*?(LTE|3G|4G|5G)(?:.*?(\d+개월\s*이후\s*[\d,]+원))?"

# #월 유무 O (1,2 통과), 매일 무 X(3번), mbps 무 X (4번)
# regex_pattern3 = r"\[(.*?)\]\s*(.*?)\s*\|\s*([\d,]+원)\s*\|\s*(?:.*?월\s*([.\d]+(?:GB|MB)\+?))?.*?매일\s*([.\d]+(?:GB|MB)).*?\(([.\d]+(?:mbps|gbps))\).*?(무제한|\d+분).*?(무제한|\d+건).*?(LG U\+|SKT|KT).*?(LTE|3G|4G|5G)(?:.*?(\d+개월\s*이후\s*[\d,]+원))?"

# #월 + 매일 + mbps O (1번), 매일 + mbps (2번) 일때 매일 안나옴, 매일 무 O (3번 통과), 월 X (4번)
# regex_pattern4 = r"\[(.*?)\]\s*(.*?)\s*\|\s*([\d,]+원)\s*\|\s*(?:.*?월\s*([.\d]+(?:GB|MB)))?(?:\s*\+\s*매일\s*([.\d]+(?:GB|MB)))?.*?\(([.\d]+(?:mbps|gbps))\).*?(무제한|\d+분).*?(무제한|\d+건).*?(LG U\+|SKT|KT).*?(LTE|3G|4G|5G)(?:.*?(\d+개월\s*이후\s*[\d,]+원))?"

# #Final Regex: 월 + 매일 + mbps O (1번), 매일 + mbps (2번) 일때 매일 안나옴, 매일 무 O (3번 통과), 월 X (4qjs)
# regex_patternZ = r"\[(.*?)\]\s*(.*?)\s*\|\s*([\d,]+원)\s*\|\s*(?:.*?월\s*([.\d]+(?:GB|MB)))?(?:\s*\+\s*매일\s*([.\d]+(?:GB|MB)))?.*?\(([.\d]+(?:mbps|gbps))\).*?(무제한|\d+분).*?(무제한|\d+건).*?(LG U\+|SKT|KT).*?(LTE|3G|4G|5G)(?:.*?(\d+개월\s*이후\s*[\d,]+원))?"



# #월 + 매일 + mbps
# sample_text1 = "[미니게이트] [모요only] 미니 LTE 11GB+  | 4,400원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지모요개통모요ONLY월 11GB + 매일 2GB데이터 다 써도 저화질 영상 재생 가능 (3mbps)무제한무제한KT망LTE 99,034명이 선택99,034명이 선택잘못된 정보 제보모요개통 요금제만의 특별혜택쿠폰 받고 요금제 개통하면 100% 지급쿠폰 이용 안내3,000원 쿠폰 받기잘못된 정보 제보월 4,400원4개월 이후 48,400원신청하기꼭 확인해 주세요가입 신청 월말까지 개통이 되지 않는 경우 신청서가 취소될 수 있습니다.지금 신청하면 언제 개통될까요?유심을 사오면유심을 사오면 오늘 바로 개통할 수 있어요평균 25분 내 개통 완료유심 사고 3만원 마트 상품권도 받아보세요유심 사러가기통신사 리뷰4.23,480개고객센터4.1개통 과정4.4개통 후 만족도4.2정*란10일 전속도나 사용경험측면에서 기존에 사용하던 대형통신사와 차이를 느낄 수 없고, 멤버쉽같은부분이 아쉬울 수 있지만 요금이 저렴하기때문에 상쇄될 수 있다고 생각합니다이*정12일 전문자에서는 현재 데이터 다 썼다고 나오고, 앱에서는 현재 사용중인 데이터양이 정확하게 나오는 거 같아요. 매번 오는 문자와 정보가 틀려 혼동스럽지만 서비스는 만족합니다.이*진23일 전서울지역인데 퀵배송지역이아니라는데 이벤트는 있는데 없는듯한 부분에서 조금 맘상했는데. 일반배송으로 빠르게 유심배송받았고 개통도 일사천리되었습니다. 만족합니다.더보기사은품 및 이벤트3대 마트 상품권 3만원대상: 1월 내 바로배송/바로유심으로 개통 후 유지시지급시기: 24년 4월말, 6월말요금제 상세 정보요금제 이름[모요only] 미니 LTE 11GB+펼쳐보기요금제 개통 절차쓰던 번호로 개통할 때새 번호로 개통할 때1. 가입 신청원하는 요금제를 찾았다면 신청 버튼을 눌러 신청서를 작성해주세요. 가입 신청을 해도 기존에 사용하던 통신사는 바로 해지되지 않아요2. 정보 확인 및 유심 배송서류를 검토한 뒤 정보가 다 올바르면 유심을 발송해요. 올바르지 않은 정보가 있었다면 통신사에서 연락을 드릴 수 있어요3. 유심 받은 후 개통 진행유심을 받으셨다면 통신사 안내에 따라 개통 요청을 해주세요. 개통이 완료되면 기존에 쓰던 통신사는 이때 자동으로 해지돼요4. 새 유심으로 갈아끼면 끝기존 통신사가 해지되고 새로운 알뜰폰 유심으로 교체하면 알뜰폰 요금제 사용이 시작돼요"

# #매일 + mbps
# sample_text2 = "[미니게이트] 미니 LTE 일 5GB+  | 19,800원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지모요개통매일 5GB데이터 다 써도 고화질 영상 재생 가능 (5mbps)무제한무제한KT망LTE 10+명이 선택10+명이 선택잘못된 정보 제보모요개통 요금제만의 특별혜택쿠폰 받고 요금제 개통하면 100% 지급쿠폰 이용 안내3,000원 쿠폰 받기잘못된 정보 제보월 19,800원4개월 이후 50,600원신청하기지금 신청하면 언제 개통될까요?유심을 사오면유심을 사오면 오늘 바로 개통할 수 있어요평균 25분 내 개통 완료유심 사고 3만원 마트 상품권도 받아보세요유심 사러가기통신사 리뷰4.23,480개고객센터4.1개통 과정4.4개통 후 만족도4.2정*란10일 전속도나 사용경험측면에서 기존에 사용하던 대형통신사와 차이를 느낄 수 없고, 멤버쉽같은부분이 아쉬울 수 있지만 요금이 저렴하기때문에 상쇄될 수 있다고 생각합니다이*정12일 전문자에서는 현재 데이터 다 썼다고 나오고, 앱에서는 현재 사용중인 데이터양이 정확하게 나오는 거 같아요. 매번 오는 문자와 정보가 틀려 혼동스럽지만 서비스는 만족합니다.이*진23일 전서울지역인데 퀵배송지역이아니라는데 이벤트는 있는데 없는듯한 부분에서 조금 맘상했는데. 일반배송으로 빠르게 유심배송받았고 개통도 일사천리되었습니다. 만족합니다.더보기사은품 및 이벤트3대 마트 상품권 3만원대상: 1월 내 바로배송/바로유심으로 개통 후 유지시지급시기: 24년 4월말, 6월말요금제 상세 정보요금제 이름미니 LTE 일 5GB+펼쳐보기요금제 개통 절차쓰던 번호로 개통할 때새 번호로 개통할 때1. 가입 신청원하는 요금제를 찾았다면 신청 버튼을 눌러 신청서를 작성해주세요. 가입 신청을 해도 기존에 사용하던 통신사는 바로 해지되지 않아요2. 정보 확인 및 유심 배송서류를 검토한 뒤 정보가 다 올바르면 유심을 발송해요. 올바르지 않은 정보가 있었다면 통신사에서 연락을 드릴 수 있어요3. 유심 받은 후 개통 진행유심을 받으셨다면 통신사 안내에 따라 개통 요청을 해주세요. 개통이 완료되면 기존에 쓰던 통신사는 이때 자동으로 해지돼요4. 새 유심으로 갈아끼면 끝기존 통신사가 해지되고 새로운 알뜰폰 유심으로 교체하면 알뜰폰 요금제 사용이 시작돼요"

# #월 + mbps
# sample_text3 = "[smartel] 5G 스마일 24GB+  | 39,600원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지월 24GB데이터 다 써도 음악 재생 가능 (1mbps)무제한무제한SKT망5G 40명이 선택40명이 선택잘못된 정보 제보잘못된 정보 제보월 39,600원신청하기요금제 상세 정보 요금제 이름스마텔 | 5G 스마일 24GB+통신사 약정없음펼쳐보기통신사 리뷰4.12,753개고객센터3.9개통 과정4.1개통 후 만족도4.3김*람22일 전기존 3사랑 서비스 면에서 똑같은데 가격은 훨씬 저렴합니다. 할인 이벤트가 끝나면 다시 통신사를 바꿔야 하는 불편함은 있지만, 그것을 감안해도 훨씬 매력적이네요이*경25일 전KT알뜰폰 쓰다넘어 왔는데 통화품질 인터녓속도 기존 kt와 다를바 없이 잘쓰고 있어요통화 상대방도 모르더라구요아주 만족해 하며 쓰고 있습니다34일 전알뜰폰 요금제를 사용한다해서 불편한점이 전혀없으며 오히려 가족들도 모두 타사의 약정이 끝나는데로  모두 알뜰 요금제로 바꿀 예정으로 있습니다. 적극추천합니다.더보기요금제 개통 절차쓰던 번호로 개통할 때새 번호로 개통할 때1. 가입 신청원하는 요금제를 찾았다면 신청 버튼을 눌러 신청서를 작성해주세요. 가입 신청을 해도 기존에 사용하던 통신사는 바로 해지되지 않아요2. 정보 확인 및 유심 배송서류를 검토한 뒤 정보가 다 올바르면 유심을 발송해요. 올바르지 않은 정보가 있었다면 통신사에서 연락을 드릴 수 있어요3. 유심 받은 후 개통 진행유심을 받으셨다면 통신사 안내에 따라 개통 요청을 해주세요. 개통이 완료되면 기존에 쓰던 통신사는 이때 자동으로 해지돼요4. 새 유심으로 갈아끼면 끝기존 통신사가 해지되고 새로운 알뜰폰 유심으로 교체하면 알뜰폰 요금제 사용이 시작돼요"

# #월
# sample_text4 = "[핀다이렉트] DIGITAL DETOX 1GB챌린지  | 4,900원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지월 1GB100분100건KT망LTE 10+명이 선택10+명이 선택잘못된 정보 제보잘못된 정보 제보월 4,900원신청 페이지로 이동통신사 리뷰4.1656개고객센터4.4개통 과정3.7개통 후 만족도4.1이*우16일 전일반 통신3사랑 다른 바 없이 동일한 서비스를 저렴한 가격에 이용할 수 있는게 가장 큰 매력입니다. 개통과정이 매우 빠른 것도 너무 좋구요 ㅎㅎ권*은20일 전해외에 가서 로밍을 할일이 있었는데 앱도 설명이 잘되어있고 쓰는 내내 잘터지고 데이터나 전화, 문자도 끊김없이 아주 잘 썼습니다 또 다른 요금제를 이용할 예정입니다 강*서27일 전이벤트가로 아주 저렴하게 써서 좋았고 태블릿으로 유튜브+넷플 많이 보는 편이라 핫스팟을 거의 항시 켜놨는데 3mbps 제외하고는 잘 터졌어요 3mbps는 솔직히 느리긴 느려요 ㅠ더보기요금제 상세 정보요금제 이름DIGITAL DETOX 1GB챌린지펼쳐보기요금제 개통 절차쓰던 번호로 개통할 때새 번호로 개통할 때1. 가입 신청원하는 요금제를 찾았다면 신청 버튼을 눌러 신청서를 작성해주세요. 가입 신청을 해도 기존에 사용하던 통신사는 바로 해지되지 않아요2. 정보 확인 및 유심 배송서류를 검토한 뒤 정보가 다 올바르면 유심을 발송해요. 올바르지 않은 정보가 있었다면 통신사에서 연락을 드릴 수 있어요3. 유심 받은 후 개통 진행유심을 받으셨다면 통신사 안내에 따라 개통 요청을 해주세요. 개통이 완료되면 기존에 쓰던 통신사는 이때 자동으로 해지돼요4. 새 유심으로 갈아끼면 끝기존 통신사가 해지되고 새로운 알뜰폰 유심으로 교체하면 알뜰폰 요금제 사용이 시작돼요"
# match = re.search(regex_patternZ, sample_text3)
# extracted_info = match.groups() if match else tuple([None] * 11)

# extracted_info

# print (extracted_info)

# import re

# # Sample texts
# sample_text1 = "[미니게이트] [모요only] 미니 LTE 11GB+ | 4,400원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지모요개통모요ONLY월 11GB + 매일 2GB데이터 다 써도 저화질 영상 재생 가능 (3mbps)무제한무제한KT망LTE 99,034명이 선택99,034명이 선택잘못된 정보 제보모요개통 요금제만의 특별혜택쿠폰 받고 요금제 개통하면 100% 지급쿠폰 이용 안내3,000원 쿠폰 받기잘못된 정보 제보월 4,400원4개월 이후 48,400원신청하기..."
# #매일 + mbps
# sample_text2 = "[미니게이트] 미니 LTE 일 5GB+  | 19,800원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지모요개통매일 5GB데이터 다 써도 고화질 영상 재생 가능 (5mbps)무제한무제한KT망LTE 10+명이 선택10+명이 선택잘못된 정보 제보모요개통 요금제만의 특별혜택쿠폰 받고 요금제 개통하면 100% 지급쿠폰 이용 안내3,000원 쿠폰 받기잘못된 정보 제보월 19,800원4개월 이후 50,600원신청하기지금 신청하면 언제 개통될까요?유심을 사오면유심을 사오면 오늘 바로 개통할 수 있어요평균 25분 내 개통 완료유심 사고 3만원 마트 상품권도 받아보세요유심 사러가기통신사 리뷰4.23,480개고객센터4.1개통 과정4.4개통 후 만족도4.2정*란10일 전속도나 사용경험측면에서 기존에 사용하던 대형통신사와 차이를 느낄 수 없고, 멤버쉽같은부분이 아쉬울 수 있지만 요금이 저렴하기때문에 상쇄될 수 있다고 생각합니다이*정12일 전문자에서는 현재 데이터 다 썼다고 나오고, 앱에서는 현재 사용중인 데이터양이 정확하게 나오는 거 같아요. 매번 오는 문자와 정보가 틀려 혼동스럽지만 서비스는 만족합니다.이*진23일 전서울지역인데 퀵배송지역이아니라는데 이벤트는 있는데 없는듯한 부분에서 조금 맘상했는데. 일반배송으로 빠르게 유심배송받았고 개통도 일사천리되었습니다. 만족합니다.더보기사은품 및 이벤트3대 마트 상품권 3만원대상: 1월 내 바로배송/바로유심으로 개통 후 유지시지급시기: 24년 4월말, 6월말요금제 상세 정보요금제 이름미니 LTE 일 5GB+펼쳐보기요금제 개통 절차쓰던 번호로 개통할 때새 번호로 개통할 때1. 가입 신청원하는 요금제를 찾았다면 신청 버튼을 눌러 신청서를 작성해주세요. 가입 신청을 해도 기존에 사용하던 통신사는 바로 해지되지 않아요2. 정보 확인 및 유심 배송서류를 검토한 뒤 정보가 다 올바르면 유심을 발송해요. 올바르지 않은 정보가 있었다면 통신사에서 연락을 드릴 수 있어요3. 유심 받은 후 개통 진행유심을 받으셨다면 통신사 안내에 따라 개통 요청을 해주세요. 개통이 완료되면 기존에 쓰던 통신사는 이때 자동으로 해지돼요4. 새 유심으로 갈아끼면 끝기존 통신사가 해지되고 새로운 알뜰폰 유심으로 교체하면 알뜰폰 요금제 사용이 시작돼요"

# #월 + mbps
# sample_text3 = "[smartel] 5G 스마일 24GB+  | 39,600원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지월 24GB데이터 다 써도 음악 재생 가능 (1mbps)무제한무제한SKT망5G 40명이 선택40명이 선택잘못된 정보 제보잘못된 정보 제보월 39,600원신청하기요금제 상세 정보 요금제 이름스마텔 | 5G 스마일 24GB+통신사 약정없음펼쳐보기통신사 리뷰4.12,753개고객센터3.9개통 과정4.1개통 후 만족도4.3김*람22일 전기존 3사랑 서비스 면에서 똑같은데 가격은 훨씬 저렴합니다. 할인 이벤트가 끝나면 다시 통신사를 바꿔야 하는 불편함은 있지만, 그것을 감안해도 훨씬 매력적이네요이*경25일 전KT알뜰폰 쓰다넘어 왔는데 통화품질 인터녓속도 기존 kt와 다를바 없이 잘쓰고 있어요통화 상대방도 모르더라구요아주 만족해 하며 쓰고 있습니다34일 전알뜰폰 요금제를 사용한다해서 불편한점이 전혀없으며 오히려 가족들도 모두 타사의 약정이 끝나는데로  모두 알뜰 요금제로 바꿀 예정으로 있습니다. 적극추천합니다.더보기요금제 개통 절차쓰던 번호로 개통할 때새 번호로 개통할 때1. 가입 신청원하는 요금제를 찾았다면 신청 버튼을 눌러 신청서를 작성해주세요. 가입 신청을 해도 기존에 사용하던 통신사는 바로 해지되지 않아요2. 정보 확인 및 유심 배송서류를 검토한 뒤 정보가 다 올바르면 유심을 발송해요. 올바르지 않은 정보가 있었다면 통신사에서 연락을 드릴 수 있어요3. 유심 받은 후 개통 진행유심을 받으셨다면 통신사 안내에 따라 개통 요청을 해주세요. 개통이 완료되면 기존에 쓰던 통신사는 이때 자동으로 해지돼요4. 새 유심으로 갈아끼면 끝기존 통신사가 해지되고 새로운 알뜰폰 유심으로 교체하면 알뜰폰 요금제 사용이 시작돼요"

# #월
# sample_text4 = "[핀다이렉트] DIGITAL DETOX 1GB챌린지  | 4,900원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지월 1GB100분100건KT망LTE 10+명이 선택10+명이 선택잘못된 정보 제보잘못된 정보 제보월 4,900원신청 페이지로 이동통신사 리뷰4.1656개고객센터4.4개통 과정3.7개통 후 만족도4.1이*우16일 전일반 통신3사랑 다른 바 없이 동일한 서비스를 저렴한 가격에 이용할 수 있는게 가장 큰 매력입니다. 개통과정이 매우 빠른 것도 너무 좋구요 ㅎㅎ권*은20일 전해외에 가서 로밍을 할일이 있었는데 앱도 설명이 잘되어있고 쓰는 내내 잘터지고 데이터나 전화, 문자도 끊김없이 아주 잘 썼습니다 또 다른 요금제를 이용할 예정입니다 강*서27일 전이벤트가로 아주 저렴하게 써서 좋았고 태블릿으로 유튜브+넷플 많이 보는 편이라 핫스팟을 거의 항시 켜놨는데 3mbps 제외하고는 잘 터졌어요 3mbps는 솔직히 느리긴 느려요 ㅠ더보기요금제 상세 정보요금제 이름DIGITAL DETOX 1GB챌린지펼쳐보기요금제 개통 절차쓰던 번호로 개통할 때새 번호로 개통할 때1. 가입 신청원하는 요금제를 찾았다면 신청 버튼을 눌러 신청서를 작성해주세요. 가입 신청을 해도 기존에 사용하던 통신사는 바로 해지되지 않아요2. 정보 확인 및 유심 배송서류를 검토한 뒤 정보가 다 올바르면 유심을 발송해요. 올바르지 않은 정보가 있었다면 통신사에서 연락을 드릴 수 있어요3. 유심 받은 후 개통 진행유심을 받으셨다면 통신사 안내에 따라 개통 요청을 해주세요. 개통이 완료되면 기존에 쓰던 통신사는 이때 자동으로 해지돼요4. 새 유심으로 갈아끼면 끝기존 통신사가 해지되고 새로운 알뜰폰 유심으로 교체하면 알뜰폰 요금제 사용이 시작돼요"


# # Define regex patterns
# mvno_pattern = r"\[(.*?)\]"
# plan_name_pattern = r"\]\s*(.*?)\s*\|"
# monthly_fee_pattern = r"\|\s*([\d,]+원)\s*\|"
# monthly_data_pattern = r"월\s*([.\d]+(?:GB|MB))"
# daily_data_pattern = r"매일\s*([.\d]+(?:GB|MB))"
# data_speed_pattern = r"\(([.\d]+(?:mbps|gbps))\)"
# call_minutes_pattern = r"(\d+분|무제한)"
# text_messages_pattern = r"(\d+건|무제한)"
# carrier_pattern = r"(LG U\+|SKT|KT)"
# network_type_pattern = r"(LTE|3G|4G|5G)"
# discount_info_pattern = r"(\d+개월\s*이후\s*[\d,]+원)"

# # Function to extract information
# def extract_info(sample_text):
#     mvno = re.search(mvno_pattern, sample_text)
#     plan_name = re.search(plan_name_pattern, sample_text)
#     monthly_fee = re.search(monthly_fee_pattern, sample_text)
#     monthly_data = re.search(monthly_data_pattern, sample_text)
#     daily_data = re.search(daily_data_pattern, sample_text)
#     data_speed = re.search(data_speed_pattern, sample_text)
#     call_minutes = re.search(call_minutes_pattern, sample_text)
#     text_messages = re.search(text_messages_pattern, sample_text)
#     carrier = re.search(carrier_pattern, sample_text)
#     network_type = re.search(network_type_pattern, sample_text)
#     discount_info = re.search(discount_info_pattern, sample_text)

#     return {
#         "MVNO": mvno.group(1) if mvno else None,
#         "요금제명": plan_name.group(1) if plan_name else None,
#         "월요금": monthly_fee.group(1) if monthly_fee else None,
#         "월 데이터(GB)": monthly_data.group(1) if monthly_data else None,
#         "일 데이터": daily_data.group(1) if daily_data else None,
#         "데이터 속도": data_speed.group(1) if data_speed else None,
#         "통화(분)": call_minutes.group(1) if call_minutes else None,
#         "문자(건)": text_messages.group(1) if text_messages else None,
#         "통신사": carrier.group(1) if carrier else None,
#         "망종류": network_type.group(1) if network_type else None,
#         "할인정보": discount_info.group(1) if discount_info else None
#     }

# # Test with the sample texts
# extracted_info1 = extract_info(sample_text4)
# # ... similar calls for other sample texts

# # Display extracted information
# print(extracted_info1)

# from random import sample
# import re
# import requests
# from bs4 import BeautifulSoup
# from urllib.parse import urljoin

# def regex_extract(strSoup):
#     # Existing patterns
#     mvno_pattern = r"\[(.*?)\]"
#     plan_name_pattern = r"\]\s*(.*?)\s*\|"
#     monthly_fee_pattern = r"\|\s*([\d,]+원)\s*\|"
#     monthly_data_pattern = r"월\s*([.\d]+(?:GB|MB))"
#     daily_data_pattern = r"매일\s*([.\d]+(?:GB|MB))"
#     data_speed_pattern = r"\(([.\d]+(?:mbps|gbps))\)"
#     call_minutes_pattern = r"(\d+분|무제한)"
#     text_messages_pattern = r"(\d+건|무제한)"
#     carrier_pattern = r"(LG U\+|SKT|KT)"
#     network_type_pattern = r"(LTE|3G|4G|5G)"
#     discount_info_pattern = r"(\d+개월\s*이후\s*[\d,]+원)"

#     # Adjusted new patterns
#     between_contract_and_call_pattern = r"(?<=통신사 약정)(.*?)(?=통화)"
#     between_number_transfer_fee_and_sim_delivery_pattern = r"(?<=번호이동 수수료)(.*?)(?=일반 유심 배송)"
#     between_nfc_sim_and_esim_pattern = r"(?<=NFC 유심 배송)(.*?)(?=eSIM)"
#     between_esim_and_support_pattern = r"(?<=eSIM)(.*?)(?=지원)"

#     # Extracting information using existing patterns
#     mvno = re.search(mvno_pattern, strSoup)
#     plan_name = re.search(plan_name_pattern, strSoup)
#     monthly_fee = re.search(monthly_fee_pattern, strSoup)
#     monthly_data = re.search(monthly_data_pattern, strSoup)
#     daily_data = re.search(daily_data_pattern, strSoup)
#     data_speed = re.search(data_speed_pattern, strSoup)
#     call_minutes = re.search(call_minutes_pattern, strSoup)
#     text_messages = re.search(text_messages_pattern, strSoup)
#     carrier = re.search(carrier_pattern, strSoup)
#     network_type = re.search(network_type_pattern, strSoup)
#     discount_info = re.search(discount_info_pattern, strSoup)

#     # Extracting information using new patterns
#     between_contract_and_call = re.search(between_contract_and_call_pattern, strSoup)
#     between_number_transfer_fee_and_sim_delivery = re.search(between_number_transfer_fee_and_sim_delivery_pattern, strSoup)
#     between_nfc_sim_and_esim = re.search(between_nfc_sim_and_esim_pattern, strSoup)
#     between_esim_and_support = re.search(between_esim_and_support_pattern, strSoup)

#     return [
#         mvno.group(1) if mvno else "제공안함", 
#         plan_name.group(1) if plan_name else "제공안함", 
#         monthly_fee.group(1) if monthly_fee else "제공안함", 
#         monthly_data.group(1) if monthly_data else "제공안함", 
#         daily_data.group(1) if daily_data else "제공안함", 
#         data_speed.group(1) if data_speed else "제공안함", 
#         call_minutes.group(1) if call_minutes else "제공안함", 
#         text_messages.group(1) if text_messages else "제공안함", 
#         carrier.group(1) if carrier else "제공안함", 
#         network_type.group(1) if network_type else "제공안함", 
#         discount_info.group(1) if discount_info else "제공안함",
#         between_contract_and_call.group(1) if between_contract_and_call else "제공안함",
#         between_number_transfer_fee_and_sim_delivery.group(1) if between_number_transfer_fee_and_sim_delivery else "제공안함",
#         between_nfc_sim_and_esim.group(1) if between_nfc_sim_and_esim else "제공안함",
#         between_esim_and_support.group(1) if between_esim_and_support else "제공안함"
#     ]


# current_url = "https://www.moyoplan.com/plans/15074"
# response = requests.get(current_url)
# soup = BeautifulSoup(response.text, 'html.parser')
# strSoup = soup.get_text()
# regex_patternZ = r"서버에 문제가 생겼어요"
# sample_text3 = strSoup
# sample_text = "[미니게이트] [모요only] 미니 LTE 11GB+ | 8,800원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지홈요금제 찾기인터넷 찾기이벤트마이페이지모요ONLY월 11GB + 매일 2GB데이터 다 써도 저화질 영상 재생 가능 (3mbps)무제한무제한KT망LTE 106,326명이 선택106,326명이 선택잘못된 정보 제보잘못된 정보 제보월 8,800원4개월 이후 48,400원신청하기꼭 확인해 주세요가입 신청 월말까지 개통이 되지 않는 경우 신청서가 취소될 수 있습니다.요금제 상세 정보 요금제 이름미니게이트 | [모요only] 미니 LTE 11GB+통신사 약정없음통화무제한문자무제한통신망KT망통신 기술LTE데이터 제공량월 11GB + 매일 2GB데이터 소진시3mbps 속도로 무제한부가통화200분번호이동 수수료800원일반 유심 배송무료NFC 유심 배송지원 안 함eSIM유료(2,750원)지원모바일 핫스팟11GB 제공데이터 쉐어링미지원인터넷 결합소액 결제해외 로밍접기통신사 리뷰4.23,480개고객센터4.1개통 과정4.4개통 후 만족도4.2정란15일 전속도나 사용경험측면에서 기존에 사용하던 대형통신사와 차이를 느낄 수 없고, 멤버쉽같은부분이 아쉬울 수 있지만 요금이 저렴하기때문에 상쇄될 수 있다고 생각합니다이정17일 전문자에서는 현재 데이터 다 썼다고 나오고, 앱에서는 현재 사용중인 데이터양이 정확하게 나오는 거 같아요. 매번 오는 문자와 정보가 틀려 혼동스럽지만 서비스는 만족합니다.이*진28일 전서울지역인데 퀵배송지역이아니라는데 이벤트는 있는데 없는듯한 부분에서 조금 맘상했는데. 일반배송으로 빠르게 유심배송받았고 개통도 일사천리되었습니다. 만족합니다.더보기사은품 및 이벤트3대 마트 상품권 3만원대상: 1월 내 바로배송/바로유심으로 개통 후 유지시지급시기: 24년 4월말, 6월말요금제 개통 절차쓰던 번호로 개통할 때새 번호로 개통할 때1. 가입 신청원하는 요금제를 찾았다면 신청 버튼을 눌러 신청서를 작성해주세요. 가입 신청을 해도 기존에 사용하던 통신사는 바로 해지되지 않아요2. 정보 확인 및 유심 배송서류를 검토한 뒤 정보가 다 올바르면 유심을 발송해요. 올바르지 않은 정보가 있었다면 통신사에서 연락을 드릴 수 있어요3. 유심 받은 후 개통 진행유심을 받으셨다면 통신사 안내에 따라 개통 요청을 해주세요. 개통이 완료되면 기존에 쓰던 통신사는 이때 자동으로 해지돼요4. 새 유심으로 갈아끼면 끝기존 통신사가 해지되고 새로운 알뜰폰 유심으로 교체하면 알뜰폰 요금제 사용이 시작돼요"
# # match = re.search(regex_patternZ, sample_text3)
# # extracted_info = match.groups() if match else tuple([None] * 11)
# extracted_info = regex_extract(sample_text3)
# print(extracted_info)

# text = "알뜰폰 요금제 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지서버에 문제가 생겼어요문제를 해결하기 위해 최선을 다하고 있어요. 잠시 후 다시 확인해주세요.다시 시도하기"
# pattern = r"서버에 문제가 생겼어요"

# # Searching for the pattern in the text
# match = re.search(pattern, text)

# # Checking if the pattern was found
# result = match.group() if match else "No match found"

# print(result)

import re

def regex_extract(strSoup):
    # Existing patterns
    mvno_pattern = r"\[(.*?)\]"
    plan_name_pattern = r"\]\s*(.*?)\s*\|"
    monthly_fee_pattern = r"\|\s*([\d,]+원)\s*\|"
    monthly_data_pattern = r"월\s*([.\d]+(?:GB|MB))"
    daily_data_pattern = r"매일\s*([.\d]+(?:GB|MB))"
    data_speed_pattern = r"\(([.\d]+(?:mbps|gbps))\)"
    call_minutes_pattern = r"(\d+분|무제한)"
    text_messages_pattern = r"(\d+건|무제한)"
    carrier_pattern = r"(LG U\+|SKT|KT)"
    network_type_pattern = r"(LTE|3G|4G|5G)"
    discount_info_pattern = r"(\d+개월\s*이후\s*[\d,]+원)"

    # Adjusted new patterns
    between_contract_and_call_pattern = r"(?<=통신사 약정)(.*?)(?=통화)"
    between_number_transfer_fee_and_sim_delivery_pattern = r"(?<=번호이동 수수료)(.*?)(?=일반 유심 배송)"
    between_nfc_sim_and_esim_pattern = r"(?<=NFC 유심 배송)(.*?)(?=eSIM)"
    between_esim_and_support_pattern = r"(?<=eSIM)(.*?)(?=지원)"

    # Extracting information using existing patterns
    mvno = re.search(mvno_pattern, strSoup)
    plan_name = re.search(plan_name_pattern, strSoup)
    monthly_fee = re.search(monthly_fee_pattern, strSoup)
    monthly_data = re.search(monthly_data_pattern, strSoup)
    daily_data = re.search(daily_data_pattern, strSoup)
    data_speed = re.search(data_speed_pattern, strSoup)
    call_minutes = re.search(call_minutes_pattern, strSoup)
    text_messages = re.search(text_messages_pattern, strSoup)
    carrier = re.search(carrier_pattern, strSoup)
    network_type = re.search(network_type_pattern, strSoup)
    discount_info = re.search(discount_info_pattern, strSoup)

    # Extracting information using new patterns
    between_contract_and_call = re.search(between_contract_and_call_pattern, strSoup)
    between_number_transfer_fee_and_sim_delivery = re.search(between_number_transfer_fee_and_sim_delivery_pattern, strSoup)
    between_nfc_sim_and_esim = re.search(between_nfc_sim_and_esim_pattern, strSoup)
    between_esim_and_support = re.search(between_esim_and_support_pattern, strSoup)

    return [
        mvno.group(1) if mvno else "제공안함", 
        plan_name.group(1) if plan_name else "제공안함", 
        monthly_fee.group(1) if monthly_fee else "제공안함", 
        monthly_data.group(1) if monthly_data else "제공안함", 
        daily_data.group(1) if daily_data else "제공안함", 
        data_speed.group(1) if data_speed else "제공안함", 
        call_minutes.group(1) if call_minutes else "제공안함", 
        text_messages.group(1) if text_messages else "제공안함", 
        carrier.group(1) if carrier else "제공안함", 
        network_type.group(1) if network_type else "제공안함", 
        discount_info.group(1) if discount_info else "제공안함",
        between_contract_and_call.group(1) if between_contract_and_call else "제공안함",
        between_number_transfer_fee_and_sim_delivery.group(1) if between_number_transfer_fee_and_sim_delivery else "제공안함",
        between_nfc_sim_and_esim.group(1) if between_nfc_sim_and_esim else "제공안함",
        between_esim_and_support.group(1) if between_esim_and_support else "제공안함"
    ]

# Example usage
strSoup = "[미니게이트] [모요only] 미니 LTE 11GB+ | 8,800원 | 모요, 모두의요금제홈요금제 찾기인터넷 찾기휴대폰 찾기이벤트마이페이지홈요금제 찾기인터넷 찾기이벤트마이페이지모요ONLY월 11GB + 매일 2GB데이터 다 써도 저화질 영상 재생 가능 (3mbps)무제한무제한KT망LTE 106,326명이 선택106,326명이 선택잘못된 정보 제보잘못된 정보 제보월 8,800원4개월 이후 48,400원신청하기꼭 확인해 주세요가입 신청 월말까지 개통이 되지 않는 경우 신청서가 취소될 수 있습니다.요금제 상세 정보 요금제 이름미니게이트 | [모요only] 미니 LTE 11GB+통신사 약정없음통화무제한문자무제한통신망KT망통신 기술LTE데이터 제공량월 11GB + 매일 2GB데이터 소진시3mbps 속도로 무제한부가통화200분번호이동 수수료800원일반 유심 배송무료NFC 유심 배송지원 안 함eSIM유료(2,750원)지원모바일 핫스팟11GB 제공데이터 쉐어링미지원인터넷 결합소액 결제해외 로밍접기통신사 리뷰4.23,480개고객센터4.1개통 과정4.4개통 후 만족도4.2정란15일 전속도나 사용경험측면에서 기존에 사용하던 대형통신사와 차이를 느낄 수 없고, 멤버쉽같은부분이 아쉬울 수 있지만 요금이 저렴하기때문에 상쇄될 수 있다고 생각합니다이정17일 전문자에서는 현재 데이터 다 썼다고 나오고, 앱에서는 현재 사용중인 데이터양이 정확하게 나오는 거 같아요. 매번 오는 문자와 정보가 틀려 혼동스럽지만 서비스는 만족합니다.이*진28일 전서울지역인데 퀵배송지역이아니라는데 이벤트는 있는데 없는듯한 부분에서 조금 맘상했는데. 일반배송으로 빠르게 유심배송받았고 개통도 일사천리되었습니다. 만족합니다.더보기사은품 및 이벤트3대 마트 상품권 3만원대상: 1월 내 바로배송/바로유심으로 개통 후 유지시지급시기: 24년 4월말, 6월말요금제 개통 절차쓰던 번호로 개통할 때새 번호로 개통할 때1. 가입 신청원하는 요금제를 찾았다면 신청 버튼을 눌러 신청서를 작성해주세요. 가입 신청을 해도 기존에 사용하던 통신사는 바로 해지되지 않아요2. 정보 확인 및 유심 배송서류를 검토한 뒤 정보가 다 올바르면 유심을 발송해요. 올바르지 않은 정보가 있었다면 통신사에서 연락을 드릴 수 있어요3. 유심 받은 후 개통 진행유심을 받으셨다면 통신사 안내에 따라 개통 요청을 해주세요. 개통이 완료되면 기존에 쓰던 통신사는 이때 자동으로 해지돼요4. 새 유심으로 갈아끼면 끝기존 통신사가 해지되고 새로운 알뜰폰 유심으로 교체하면 알뜰폰 요금제 사용이 시작돼요"
results = regex_extract(strSoup)
print(results)
