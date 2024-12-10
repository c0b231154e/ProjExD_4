import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm

class EMP(pg.sprite.Sprite):
    #EMP実装に関してのクラス
    def __init__(self, enemies: pg.sprite.Group, bombs: pg.sprite.Group, screen):
        """
        EMPの初期設定を行う
        引数1 enemies: 敵機グループ
        引数2 bombs: 爆弾グループ
        """
        for enemy in enemies:
            enemy.interval = math.inf
            enemy.state = "inactive"
            enemy.image = pg.transform.laplacian(enemy.image)
        
        for bomb in bombs:
            bomb.speed /= 2  # 爆弾の速度を半減
            bomb.state = "inactive"  # 爆弾を無効化

        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        overlay.fill((255, 255, 0, 128))  # 半透明の黄色
        screen.blit(overlay, (0, 0))

        pg.display.update()

    # def update(self, screen: pg.Surface):
    #     """
    #     EMPの状態を更新し、画面にエフェクトを描画する
    #     """
    #     if self.active:
    #         self.timer -= 1
    #         # 黄色いエフェクトを画面全体に描画
    #         overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
    #         overlay.fill((255, 255, 0, 128))  # 半透明の黄色
    #         screen.blit(overlay, (0, 0))
    #         if self.timer <= 0:
    #             self.active = False  # 効果終了
            
                     
class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]
        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)  
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6
        self.state = "active"

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class NeoBeam:
    """
    複数方向ビームを生成するクラス
    """
    def __init__(self, bird: Bird, num: int):
        """
        NeoBeamの初期化
        引数bird：ビームを発射するこうかとん
        引数num：発射するビームの数
        """
        self.bird = bird
        self.num = num

    def gen_beams(self):
        """
        指定されたビーム数だけ異なる角度でビームを生成しリストを返す
        """
        beams = []
        for i in range(-50, +51, 100//(self.num-1)):
            beam = Beam(self.bird, i)
            beams.append(beam)
        return beams


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0: float = 0.0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        引数 angle0：初期角度
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        base_angle = math.degrees(math.atan2(-self.vy, self.vx))
        angle = base_angle + angle0
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル
    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)




class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Shield(pg.sprite.Sprite):
    """
    防御壁に関するクラス
    """
    def __init__(self, bird: Bird, life: int):
        """
        防御壁を生成する
        引数1 bird：防御壁を設置するこうかとん
        引数2 life：防御壁の寿命
        """
        super().__init__()
        self.life = life

        self.image = pg.Surface((20, bird.rect.height * 2), pg.SRCALPHA)
    
        pg.draw.rect(self.image, (0, 0, 255), (0, 0, 20, bird.rect.height * 2))
        vx, vy = bird.dire
        angle = math.degrees(math.atan2(-vy, vx))
        self.image = pg.transform.rotozoom(self.image, angle, 1.0)
        self.rect = self.image.get_rect()
        offset_x = vx * bird.rect.width
        offset_y = vy * bird.rect.height
        self.rect.centerx = bird.rect.centerx + offset_x
        self.rect.centery = bird.rect.centery + offset_y

    def update(self):

        self.life -= 1
        if self.life < 0:
            self.kill()

class Gravity(pg.sprite.Sprite):
    """
    重力場を表現するクラス
    """
    def __init__(self, life: int):
        """
        半透明の重力場を作成する
        引数 life: 重力場の寿命（フレーム数）
        """
        super().__init__()
        self.image = pg.Surface((WIDTH, HEIGHT))  # 画面全体のSurface
        self.image.fill((0, 0, 0))  # 黒色で塗りつぶす
        self.image.set_alpha(128)  # 透明度を設定（0:完全透明, 255:不透明）
        self.rect = self.image.get_rect()
        self.life = life

    def update(self, bombs: pg.sprite.Group, emys: pg.sprite.Group, screen: pg.Surface, exps: pg.sprite.Group, score: int):
        """
        重力場の寿命を減少させ、範囲内の爆弾と飛行船を撃墜する
        引数 bombs: 爆弾のスプライトグループ
        引数 emys: 飛行船のスプライトグループ
        引数 screen: 画面Surface
        引数 exps: 爆発エフェクトのスプライトグループ
        引数 score: スコアオブジェクト
        """
        for bomb in bombs:
            # 爆弾を削除し、爆発エフェクトを追加
            exps.add(Explosion(bomb, 50))
            score.value += 1  # スコアを加算
            bomb.kill()

        for emy in emys:
            # 飛行船を削除し、爆発エフェクトを追加
            exps.add(Explosion(emy, 100))
            score.value += 10  # スコアを加算
            emy.kill()

        self.life -= 1
        if self.life <= 0:  # 寿命が尽きたら削除
            self.kill()
        screen.blit(self.image, self.rect)  # 重力場を描画


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load(f"fig/pg_bg.jpg")
    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    gravities = pg.sprite.Group()  # 重力場のスプライトグループ

    shields = pg.sprite.Group()  

    tmr = 0
    emp = None
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key ==pg.K_e and score.value >= 1:
                EMP(emys, bombs, screen)  # スコアが20以上ならEMP発動
                score.value -= 1  # スコアを消費


            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))
                if event.key == pg.K_g and score.value >= 200:  # Gキーで重力場を発動
                    gravities.add(Gravity(400))
                    score.value -= 200  # スコアを消費

            if event.type == pg.KEYDOWN:
                if pg.key.get_pressed()[pg.K_LSHIFT]:
                    if event.key == pg.K_SPACE:
                        neo_beam = NeoBeam(bird, 10)  # 5方向ビームを生成
                        beams.add(*neo_beam.gen_beams())
                else:
                    if event.key == pg.K_SPACE:
                        beams.add(Beam(bird))
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))  # ビーム発射
                if event.key == pg.K_s:
                    if score.value >= 50 and not shields:
                        shields.add(Shield(bird, 400))  
                        score.value -= 50  

        screen.blit(bg_img, [0, 0])

        if tmr % 200 == 0:  # 200フレームに1回、敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0:
                bombs.add(Bomb(emy, bird))

        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機
            exps.add(Explosion(emy, 100))
            score.value += 10
            bird.change_img(6, screen)

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ
        
        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト

            if bomb.state == "inactive":
                continue
            bird.change_img(8, screen)  # こうかとん悲しみエフェクト
            score.update(screen)
            pg.display.update()
            time.sleep(2)
            return
        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾
            exps.add(Explosion(bomb, 50))
            score.value += 1

        # 各要素の更新
        for shield in pg.sprite.groupcollide(shields, bombs, False, True).keys():
            exps.add(Explosion(shield, 30))  # 衝突時に爆発エフェクト

        # 各オブジェクトの更新と描画
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        gravities.update(bombs, emys, screen, exps, score)  # 重力場の更新
        exps.update()
        exps.draw(screen)
        shields.update()  
        shields.draw(screen)  
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()