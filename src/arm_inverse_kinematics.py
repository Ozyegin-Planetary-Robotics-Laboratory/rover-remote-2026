import math

# =========================================================
# 4 DOF rover arm inverse kinematics
# =========================================================
# burda olay şu:
# 1) önce x,y den base yaw bulcaz
# 2) sonra 3 boyutu r-z duzlemine indiricez
# 3) sonra 2 link gibi shoulder elbow cozcez
# 4) en son wrist i de toplama gore ayarlıcaz
#
# not:
# bu kodda acilar RADYAN olarak donuyor
# ekrana bastırırken dereceye ceviriyoz
#
# repodaki uzunluklar:
# SEGMENTS = [0.48065, 0.42053, 0.40736]
# yani:
# L1 = shoulder -> elbow
# L2 = elbow -> wrist
# L3 = wrist -> end effector
# =========================================================

L1 = 0.48065
L2 = 0.42053
L3 = 0.40736

# joint limitleri repo mantığına gore derece olarak yazdim
# sonra rad a ceviricem
DOF_LIMITS_DEG = {
    1: (-135.0, 135.0),   # base yaw
    2: (-15.0, 90.0),     # shoulder
    3: (-15.0, 135.0),    # elbow
    4: (-15.0, 110.0),    # wrist
}

DOF_LIMITS_RAD = {
    dof: (math.radians(mn), math.radians(mx))
    for dof, (mn, mx) in DOF_LIMITS_DEG.items()
}


def clamp(value, low, high):
    # bazen float yüzünden 1.00000002 falan oluyo
    # acos patlamasın diye sıkıştırıyoruz
    return max(low, min(high, value))


def normalize_angle_rad(angle):
    # acıyı -pi ile pi arasına getirioz
    # boyle daha temiz oluyo
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


def rad_to_deg(angle_rad):
    return math.degrees(angle_rad)


def deg_to_rad(angle_deg):
    return math.radians(angle_deg)


def pretty_print_solution(theta_dict):
    # guzel dursun diye
    print("==== IK SONUCU ====")
    print(f"DOF1 base     : {rad_to_deg(theta_dict[1]):8.3f} deg")
    print(f"DOF2 shoulder : {rad_to_deg(theta_dict[2]):8.3f} deg")
    print(f"DOF3 elbow    : {rad_to_deg(theta_dict[3]):8.3f} deg")
    print(f"DOF4 wrist    : {rad_to_deg(theta_dict[4]):8.3f} deg")
    print()


def check_joint_limits(theta_dict):
    # repo da limitler var, biz de cozumden sonra bakıyoz
    # eger limit dısıysa hata veriyoruz
    for dof, angle in theta_dict.items():
        mn, mx = DOF_LIMITS_RAD[dof]
        if angle < mn or angle > mx:
            raise ValueError(
                f"DOF{dof} limit disi kaldi. "
                f"aci = {rad_to_deg(angle):.3f} deg, "
                f"limit = [{rad_to_deg(mn):.3f}, {rad_to_deg(mx):.3f}] deg"
            )


def forward_kinematics_4dof(theta1, theta2, theta3, theta4):
    """
    ileri kinematik
    bunu test icin yazıyoruz
    ik den buldugumuz acilar gercekten hedefe gidiyo mu diye bakcaz

    theta1 = base yaw
    theta2 = shoulder
    theta3 = elbow
    theta4 = wrist

    donus:
    x, y, z, phi

    phi = planar pitch gibi dusun
    """

    # planar kısımda toplam acılar
    a1 = theta2
    a2 = theta2 + theta3
    a3 = theta2 + theta3 + theta4

    # dikkat:
    # repo daki 2d fonksiyonda x tarafı sin, y tarafı cos gibi yazılmış
    # ben burda onu r-z diye dusundum
    # r = yataydaki uzanım
    # z = yukseklik
    r = (
        L1 * math.sin(a1) +
        L2 * math.sin(a2) +
        L3 * math.sin(a3)
    )

    z = (
        L1 * math.cos(a1) +
        L2 * math.cos(a2) +
        L3 * math.cos(a3)
    )

    # sonra bu r yi yaw ile 3d ye aciyoruz
    x = r * math.cos(theta1)
    y = r * math.sin(theta1)

    phi = a3

    return x, y, z, phi


def inverse_kinematics_4dof(x, y, z, phi, elbow_up=False):
    """
    asil baba fonksiyon bu

    girisler:
    x, y, z  -> hedef nokta
    phi      -> end effector planar pitch acısı (radyan)
    elbow_up -> iki cozumden hangisini alıcağımız

    cikis:
    {1: theta1, 2: theta2, 3: theta3, 4: theta4}
    """

    # -----------------------------------------------------
    # 1) base yaw
    # -----------------------------------------------------
    # yukardan bakınca hedef hangi yoneyse oraya donuyor
    theta1 = math.atan2(y, x)

    # -----------------------------------------------------
    # 2) 3d -> 2d indirgeme
    # -----------------------------------------------------
    # yatay duzlemde hedefin merkeze olan uzaklıgı
    r = math.sqrt(x * x + y * y)

    # -----------------------------------------------------
    # 3) wrist center bulma
    # -----------------------------------------------------
    # son linki cıkarıyoruz cunku shoulder+elbow once
    # wrist merkezine gitcek
    #
    # fk de:
    # r = ... + L3*sin(phi)
    # z = ... + L3*cos(phi)
    #
    # o yuzden:
    rw = r - L3 * math.sin(phi)
    zw = z - L3 * math.cos(phi)

    # -----------------------------------------------------
    # 4) reachability kontrolu
    # -----------------------------------------------------
    # wrist center 2 link ile ulasılabiliyor mu
    d2 = rw * rw + zw * zw
    cos_theta3 = (d2 - L1 * L1 - L2 * L2) / (2.0 * L1 * L2)

    # float hatasına ragmen once bi gercekten sacma mı bakıyoruz
    if cos_theta3 < -1.000001 or cos_theta3 > 1.000001:
        raise ValueError(
            "Bu hedefe kol ulasamıyo gibi. "
            f"cos(theta3) = {cos_theta3}"
        )

    cos_theta3 = clamp(cos_theta3, -1.0, 1.0)

    # -----------------------------------------------------
    # 5) elbow acısı
    # -----------------------------------------------------
    # iki cozum var:
    # elbow-up ve elbow-down
    if elbow_up:
        theta3 = -math.acos(cos_theta3)
    else:
        theta3 = math.acos(cos_theta3)

    # -----------------------------------------------------
    # 6) shoulder acısı
    # -----------------------------------------------------
    # klasik 2 link IK formulu
    # atan2(rw, zw) kullandım cunku bizim duzende
    # yukseklik z tarafında cos ile gidiyodu
    theta2 = math.atan2(rw, zw) - math.atan2(
        L2 * math.sin(theta3),
        L1 + L2 * math.cos(theta3)
    )

    # -----------------------------------------------------
    # 7) wrist acısı
    # -----------------------------------------------------
    # toplam pitch phi olcak diye wrist i ayarlıyoruz
    theta4 = phi - theta2 - theta3

    # -----------------------------------------------------
    # 8) acıları normalize et
    # -----------------------------------------------------
    theta1 = normalize_angle_rad(theta1)
    theta2 = normalize_angle_rad(theta2)
    theta3 = normalize_angle_rad(theta3)
    theta4 = normalize_angle_rad(theta4)

    solution = {
        1: theta1,
        2: theta2,
        3: theta3,
        4: theta4
    }

    # -----------------------------------------------------
    # 9) joint limit kontrolu
    # -----------------------------------------------------
    check_joint_limits(solution)

    return solution


def inverse_kinematics_with_auto_phi(x, y, z, preferred_phi_deg=0.0, elbow_up=False):
    """
    bazen hoca sadece x y z ister
    phi vermez
    o zaman bi default phi secmek lazım
    yoksa sonsuz tane cozum olabilir

    preferred_phi_deg:
    0 dersen uc efektor yukarı gibi kalır
    20 dersen hafif on tarafa bakar
    -20 dersen biraz aşağı bakar
    """
    phi = deg_to_rad(preferred_phi_deg)
    return inverse_kinematics_4dof(x, y, z, phi, elbow_up=elbow_up)


def verify_solution(theta_dict, target_x, target_y, target_z, target_phi):
    """
    cozumu geri ileri kinematikten kontrol ediyoruz
    cok tatlı sey bu
    ik ile bul -> fk ye sok -> tekrar hedefe yakın mı bak
    """

    x_fk, y_fk, z_fk, phi_fk = forward_kinematics_4dof(
        theta_dict[1], theta_dict[2], theta_dict[3], theta_dict[4]
    )

    print("==== FK KONTROL ====")
    print(f"hedef x   : {target_x:.6f}")
    print(f"hesap x   : {x_fk:.6f}")
    print(f"fark x    : {x_fk - target_x:.6f}")
    print()

    print(f"hedef y   : {target_y:.6f}")
    print(f"hesap y   : {y_fk:.6f}")
    print(f"fark y    : {y_fk - target_y:.6f}")
    print()

    print(f"hedef z   : {target_z:.6f}")
    print(f"hesap z   : {z_fk:.6f}")
    print(f"fark z    : {z_fk - target_z:.6f}")
    print()

    print(f"hedef phi : {rad_to_deg(target_phi):.6f} deg")
    print(f"hesap phi : {rad_to_deg(phi_fk):.6f} deg")
    print(f"fark phi  : {rad_to_deg(phi_fk - target_phi):.6f} deg")
    print()


# =========================================================
# arm_server.py ye koymak istersen kullanabilecegin helper
# =========================================================
def solve_target_for_repo(x, y, z, phi_deg=0.0, elbow_up=False):
    """
    bunu serverdan falan cagırırsın
    direkt dof dictionary doner

    not:
    rad donuyor cunku matematikte daha temiz
    motor komutuna gecmeden once dereceye cevirirsin
    """
    phi = deg_to_rad(phi_deg)
    return inverse_kinematics_4dof(x, y, z, phi, elbow_up=elbow_up)


def solution_rad_to_deg_dict(theta_dict):
    # ui ye derece basmak istersen diye
    return {dof: rad_to_deg(angle) for dof, angle in theta_dict.items()}


# =========================================================
# test kısmı
# =========================================================
if __name__ == "__main__":
    # ornek hedef
    # bunlar tamamen deneme
    # eger limit dışına cıkarsa sayıalrı değiştir
    x_target = 0.35
    y_target = 0.10
    z_target = 0.95

    # phi:
    # 0 derece = uc taraf yukarı referans gibi
    # ama bu tanım bizim kurdugumuz modeldeki planar pitch
    phi_target_deg = 10.0
    phi_target = deg_to_rad(phi_target_deg)

    try:
        # elbow_up false dedim
        # öbür cozumu istersen true yap
        sol = inverse_kinematics_4dof(
            x=x_target,
            y=y_target,
            z=z_target,
            phi=phi_target,
            elbow_up=False
        )

        pretty_print_solution(sol)

        print("derece dictionary:")
        print(solution_rad_to_deg_dict(sol))
        print()

        verify_solution(sol, x_target, y_target, z_target, phi_target)

    except ValueError as e:
        print("IK patladı / hata verdi:")
        print(e)
