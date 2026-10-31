#!/usr/bin/env python3
"""Build web/classbuster.wad from Freedoom (Phase 1) + CLASS BUSTER replacement art.
usage: python3 tools/build_wad.py path/to/freedoom1.wad web/classbuster.wad"""
import sys, time
import numpy as np
from wadlib import Wad, Palette, picture_from_rgba
import art2d as A2
import art3d as A3

MENU = {
    'M_NGAME': '새 게임', 'M_OPTION': '설정', 'M_LOADG': '불러오기', 'M_SAVEG': '저장하기',
    'M_RDTHIS': '도움말', 'M_QUITG': '종료', 'M_NEWG': '새 게임', 'M_SKILL': '난이도를 고르시오:',
    'M_EPISOD': '학기를 고르시오:', 'M_JKILL': '연습 문제', 'M_ROUGH': '쪽지 시험', 'M_HURT': '중간고사',
    'M_ULTRA': '기말고사', 'M_NMARE': '심화 도전', 'M_EPI1': '1학기: 본관', 'M_EPI2': '2학기: 과학관',
    'M_EPI3': '3학기: 시험장', 'M_EPI4': '4학기: 방학', 'M_PAUSE': '일시정지', 'M_ENDGAM': '게임 끝내기',
    'M_MESSG': '메시지:', 'M_MSGON': '켜짐', 'M_MSGOFF': '꺼짐', 'M_DETAIL': '화질:', 'M_GDHIGH': '높음',
    'M_GDLOW': '낮음', 'M_SCRNSZ': '화면 크기', 'M_MSENS': '마우스 감도', 'M_SVOL': '음량',
    'M_SFXVOL': '효과음', 'M_MUSVOL': '배경음악', 'M_OPTTTL': '설정', 'M_SGTTL': '저장하기', 'M_LGTTL': '불러오기',
    'M_DISOPT': '화면 설정', 'M_SOUND': '소리 설정', 'M_DISP': '디스플레이', 'M_GENERL': '일반 설정',
    'M_SETUP': '환경 설정', 'M_KEYBND': '키 설정', 'M_WEAP': '도구 설정', 'M_STAT': '상태 표시',
    'M_AUTO': '자동 지도', 'M_ENEM': '대상 정보', 'M_MESS': '메시지 설정', 'M_CHAT': '대화 설정', 'M_CHATM': '대화 모드',
    'M_HORSEN': '조준점', 'M_VERSEN': '버전 정보', 'M_LOKSEN': '잠금 감도', 'M_ACCEL': '마우스 가속',
    'M_ABOUT': '게임 정보', 'M_COMPAT': '호환 설정', 'M_DEMOS': '플레이 기록', 'M_DMFLAG': '게임 규칙',
    'M_ETCOPT': '기타 설정', 'M_FEAT': '기능 설정', 'M_GSET': '게임 설정', 'M_HUD': '상태 표시',
    'M_JOYSET': '컨트롤러', 'M_LDSV': '저장·불러오기', 'M_MENUS': '메뉴 설정', 'M_MOUSE': '마우스 설정',
    'M_MULTI': '멀티플레이', 'M_PLAYER': '플레이어', 'M_SERIAL': '연결 설정', 'M_STATUS': '진행 상태',
    'M_TCPIP': '네트워크', 'M_VIDEO': '화면 설정', 'M_WAD': '게임 데이터', 'M_WADOPT': '데이터 설정',
    'M_CRISPY': 'Crispy Doom',
}
TITLES = {'M_OPTTTL', 'M_SGTTL', 'M_LGTTL', 'M_NEWG', 'M_PAUSE', 'M_DISOPT', 'M_SETUP'}
LEVELS = [
    ['교문 앞', '1층 복도', '교무실', '컴퓨터실', '급식실', '도서관', '강당', '옥상', '비밀 창고'],
    ['과학관 입구', '화학 실험실', '생물 실험실', '물리 실험실', '천체 관측실', '온실', '준비실', '기계실', '표본 보관실'],
    ['시험장 복도', '문제 은행', '채점실', '성적 처리실', '답안지 창고', '감독 교실', '시험 본부', '최종 평가실', '비밀 오답 노트'],
    ['보충 수업실', '탐구 교실', '독서실', '야간 자습실', '모의고사장', '체육관', '운동장', '졸업식장', '동아리 연구실'],
]
WI = {
    'WIF': '완료!', 'WIENTER': '다음 구역', 'WIOSTK': '완료율', 'WIOSTI': '아이템',
    'WISCRT2': '비밀', 'WIOSTS': '비밀', 'WITIME': '시간', 'WIPAR': '기준',
    'WISUCKS': '초과', 'WIMSTT': '합계', 'WIFRGS': '점수'
}



def customize(w, dst):
    t0 = time.time()
    pal = Palette(w.get('PLAYPAL'))
    have = set(w.names())

    def put(name, data):
        if name in have:
            w.set(name, data)

    def fitted_patch(name, txt, preferred=14, stops=A2.ACADEMIC_CYAN):
        old = w.get(name)
        maxw = 180
        if old and len(old) >= 8:
            import struct
            maxw = max(18, struct.unpack('<hhhh', old[:8])[0])
        size = preferred
        while size > 7:
            data, tw, th = A2.patch_text(pal, txt, size, stops=stops)
            if tw <= maxw:
                return data
            size -= 1
        return A2.patch_text(pal, txt, 7, stops=stops)[0]

    # ---- menu graphics
    for k, txt in MENU.items():
        if k not in have:
            continue
        size = 17 if k in TITLES else 13
        stops = A2.GOLD if k in TITLES else A2.ACADEMIC_CYAN
        put(k, fitted_patch(k, txt, size, stops))
    logo = A2.logo_rgba(0.82)
    put('M_DOOM', picture_from_rgba(pal, logo, logo.shape[1] // 2 - 66, 0, 110))
    # ---- intermission
    for e, names in enumerate(LEVELS):
        for m, nm in enumerate(names):
            data = fitted_patch(f'WILV{e}{m}', nm, 12, A2.ACADEMIC_CYAN)
            put(f'WILV{e}{m}', data)
    for k, txt in WI.items():
        if k in have:
            put(k, fitted_patch(k, txt, 12, A2.GOLD))
    star = A2.text_rgba('★', 16, A2.GOLD, A2.FONT_HEAVY, stroke=1, outline='#402000', shadow=0)
    put('WISPLAT', picture_from_rgba(pal, star, star.shape[1] // 2, star.shape[0] // 2, 110))
    # ---- full screens
    put('TITLEPIC', A2.full_rgb_to_pic(pal, A2.titlepic()))
    hp = A2.full_rgb_to_pic(pal, A2.help_screen())
    put('HELP1', hp); put('HELP2', hp); put('HELP', hp)
    put('CREDIT', A2.full_rgb_to_pic(pal, A2.credit_screen()))
    put('VICTORY2', A2.full_rgb_to_pic(pal, A2.ending_screen('VICTORY2')))
    put('ENDPIC', A2.full_rgb_to_pic(pal, A2.ending_screen('ENDPIC')))
    put('PFUB1', A2.full_rgb_to_pic(pal, A2.panorama(1)))
    put('PFUB2', A2.full_rgb_to_pic(pal, A2.panorama(0)))
    print('menus/screens', round(time.time() - t0, 1), 's')
    # ---- faces, walls, sounds, sprites
    print('faces', A2.build_faces(w, pal))
    print('weapons', A2.build_weapon_sprites(w, pal))
    put('STBAR', A2.statusbar_art(pal))
    put('STARMS', A2.statusbar_side_art(pal, 'STARMS'))
    for i in range(9):
        k = f'STKEYS{i}'
        if k in have:
            import struct
            old = w.get(k)
            ow, oh = struct.unpack('<hhhh', old[:8])[:2] if old and len(old) >= 8 else (7, 7)
            put(k, A2.statusbar_side_art(pal, k, ow, oh))
    print('walls/flats', A2.build_walls(w, pal))
    for k, data in A2.sounds().items():
        put(k, data)
    print('sounds done')
    A3.build_sprites(w, pal)
    w.save(dst)
    print('wrote', dst, round(time.time() - t0, 1), 's')


def main(src, dst):
    return customize(Wad(src), dst)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: python3 tools/build_wad.py input.wad output.wad')
    main(sys.argv[1], sys.argv[2])
