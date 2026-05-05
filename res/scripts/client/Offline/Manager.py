import BigWorld
import new
import traceback
import AccountCommands
import account_helpers.AccountSettings as AS
from ConnectionManager import connectionManager
from PlayerEvents import g_playerEvents
from items import tankmen
_modules_inventory = {}
_modules_by_type   = {}

def init_offline():
    from gui.Scaleform import VoiceChatInterface
    VoiceChatInterface.g_instance._VoiceChatInterface__state = 2
    print "[OFFLINE] World of Tanks Start ! "

    def fake_connect(*args, **kwargs):
        global _modules_inventory, _modules_by_type

        try:
            connectionManager.connectionStatusCallbacks(1, 'LOGGED_ON', '')

            try:
                from gui import SoundGroups
                if SoundGroups.g_instance: SoundGroups.g_instance.stopAll()
            except: pass

            spaceID = BigWorld.createSpace()
            from items import vehicles
            import nations

            tank_list = [
                'ussr:MS-1','ussr:A-32','ussr:AT-1','ussr:BT-2','ussr:BT-7','ussr:Churchill_LL','ussr:GAZ-74b','ussr:IS',
                'ussr:IS-3','ussr:IS-4','ussr:IS-7','ussr:ISU-152','ussr:KV','ussr:KV-1s','ussr:KV-3','ussr:KV-220',
                'ussr:M3_Stuart_LL','ussr:Matilda_II_LL','ussr:A-20','ussr:Object_212','ussr:Object_704','ussr:S-51','ussr:SU-5','ussr:SU-8',
                'ussr:SU-14','ussr:SU-18','ussr:SU-26','ussr:SU-76','ussr:SU-85','ussr:SU-100','ussr:SU-152','ussr:T-26',
                'ussr:T-28','ussr:T-34','ussr:T-34-85','ussr:T-43','ussr:T-44','ussr:T-46','ussr:T-54','ussr:Valentine_LL',
                'ussr:Object_261','ussr:KV-13','ussr:T-50','ussr:T_50_2','ussr:T-127','ussr:BT-SV','ussr:KV-5',
                
                'germany:B-1bis_captured','germany:Bison_I','germany:Ferdinand','germany:G_Panther','germany:Sturmpanzer_II','germany:G_Tiger','germany:G20_Marder_II','germany:Grille',
                'germany:H39_captured','germany:Hetzer','germany:Hummel','germany:JagdPanther','germany:JagdPzIV','germany:JagdTiger','germany:Ltraktor','germany:Maus',
                'germany:Panther_II','germany:PanzerJager_I','germany:Pz35t','germany:Pz38t','germany:PzII','germany:PzII_Luchs','germany:PzIII','germany:PzIII_A',
                'germany:PzIII_IV','germany:PzIV','germany:PzV','germany:PzV_PzIV','germany:PzV_PzIV_ausf_Alfa','germany:PzVI','germany:PzVIB_Tiger_II','germany:StuGIII',
                'germany:VK1602','germany:VK3001H','germany:VK3001P','germany:VK3002DB','germany:VK3601H','germany:VK4502P','germany:Wespe',
                'germany:G_E','germany:E-50','germany:E-75','germany:E-100','germany:PzVI_Tiger_P','germany:Lowe','germany:T-15','germany:T-25','germany:S35_captured',
                'germany:Pz38_NA','germany:PzII_J','germany:VK2801','germany:VK4502A',
                
                'usa:M2_lt','usa:M2_med','usa:M3_Grant','usa:M3_Stuart','usa:M4_Sherman','usa:M4A3E8_Sherman','usa:M5_Stuart','usa:M6',
                'usa:M7_med','usa:M7_Priest','usa:M12','usa:M37','usa:M40M43','usa:M41','usa:Pershing','usa:Ram-II',
                'usa:T1_Cunningham','usa:T1_hvy','usa:T2_lt','usa:T2_med','usa:T14','usa:T20','usa:T23',
                'usa:T29','usa:T30','usa:T32','usa:T34_hvy','usa:T57','usa:T92','usa:M4A2E4','usa:M46_Patton','usa:M24_Chaffee',
                'usa:T18','usa:T82','usa:T40','usa:M10_Wolverine','usa:M36_Slagger','usa:T25_AT','usa:T28','usa:T95','usa:M22_Locust','usa:Sherman_Jumbo',
                'usa:M6A2E1',
                
                'china:Ch01_Type59',
            ]

            my_garage = {}
            veh_cds   = {}
            for i, name in enumerate(tank_list):
                invID = i + 1
                my_garage[invID] = name
                try:
                    veh_cds[invID] = vehicles.VehicleDescr(typeName=name).makeCompactDescr()
                except Exception as e:
                    print "[OFFLINE] Error loading %s: %s" % (name, e)

            all_unlocks = []
            for nID in range(len(nations.NAMES)):
                try:
                    vList = vehicles.g_list.getList(nID)
                    for vID in vList.keys():
                        all_unlocks.append(vehicles.makeIntCompactDescrByID('vehicle', nID, vID))
                except: continue

            inv_vehicles = dict((invID, cd) for invID, cd in veh_cds.items())

            t_cache        = {}
            t_in_veh       = {}
            crew_map       = {}
            current_tman_id = 10

            for invID, name in my_garage.items():
                if invID not in veh_cds: continue
                descr      = vehicles.VehicleDescr(compactDescr=veh_cds[invID])
                crew_ids   = []
                nationID   = descr.type.id[0]
                vehTypeID  = descr.type.id[1]

                for role in descr.type.crewRoles:
                    passport = tankmen.generatePassport(nationID)
                    tman_cd  = tankmen.generateCompactDescr(passport, vehTypeID, role[0], 100)
                    t_cache[current_tman_id]  = tman_cd
                    t_in_veh[current_tman_id] = invID
                    crew_ids.append(current_tman_id)
                    current_tman_id += 1
                crew_map[invID] = crew_ids

            _modules_inventory = {}
            _modules_by_type   = {}

            for nationID in range(len(nations.NAMES)):
                try:
                    for gun in vehicles.g_cache.guns(nationID).values():
                        cd = gun.get('compactDescr')
                        if cd:
                            _modules_inventory[cd] = 1
                            _modules_by_type.setdefault(4, {})[cd] = 1
                    for turret in vehicles.g_cache.turrets(nationID).values():
                        cd = turret.get('compactDescr')
                        if cd:
                            _modules_inventory[cd] = 1
                            _modules_by_type.setdefault(3, {})[cd] = 1
                    for engine in vehicles.g_cache.engines(nationID).values():
                        cd = engine.get('compactDescr')
                        if cd:
                            _modules_inventory[cd] = 1
                            _modules_by_type.setdefault(5, {})[cd] = 1
                    for chassis in vehicles.g_cache.chassis(nationID).values():
                        cd = chassis.get('compactDescr')
                        if cd:
                            _modules_inventory[cd] = 1
                            _modules_by_type.setdefault(2, {})[cd] = 1
                    for radio in vehicles.g_cache.radio(nationID).values():
                        cd = radio.get('compactDescr')
                        if cd:
                            _modules_inventory[cd] = 1
                            _modules_by_type.setdefault(1, {})[cd] = 1
                    
                except Exception as e:
                    pass

            print "[OFFLINE] Loaded %d modules" % len(_modules_inventory)

            inv_data = [
                inv_vehicles,
                dict((i, {})         for i in my_garage),
                dict((i, [])         for i in my_garage),
                crew_map,
                dict((i, (0, 100))   for i in my_garage),
                dict((i, [0, 0, 0])  for i in my_garage),
                dict((i, [0, 0, 0])  for i in my_garage),
                dict((i, 0)          for i in my_garage),
                dict((i, 0)          for i in my_garage)
            ]

            off_stats = {
                'credits':          100000000,
                'gold':             100000000,
                'freeXP':           100000000,
                'vehTypeXP':        {}, 
                'tkillIsSuspected': False, 
                'restrictions':     0,
                'clanInfo':         None,
                'unlocks':          all_unlocks + list(_modules_inventory.keys()),
                'eliteVehicles':    all_unlocks,
                'rev':              1,
                'slots':            150,
                'berths':           100,
                'currentVehInvID':  1,
                'isPremium':        True,
                'premiumExpiryTime':1999999999,
                'attrs': 0,
                'dossier': '', 
                'doubleXPVehs': [],
            }

            if not BigWorld.player():
                BigWorld.createEntity('Account', spaceID, 0, (0, 0, 0), (0, 0, 0), {'serverSettings': {'vivoxDomain': ''}})
                p = BigWorld.player()
                p.name = 'wot_13062011'

                import CurrentVehicle

                class OfflineVehicleWrapper(object):
                    def __init__(self, invID):
                        self.inventoryId  = invID
                        self.descriptor   = vehicles.VehicleDescr(compactDescr=veh_cds[invID])
                        self.level        = self.descriptor.level
                        self.crew         = [(tid, idx) for idx, tid in enumerate(crew_map[invID])]
                        self.health       = 100
                        self.modelState   = 'undamaged'
                        self.lock         = 0
                        self.isElite      = True
                        self.tags         = self.descriptor.type.tags
                        self.shells       = []
                        self.equipments   = [0, 0, 0]
                        self.repairCost   = 0
                    def __getattr__(self, n): return None

                def call_smart(cb, data):
                    if not cb: return
                    import inspect
                    try:
                        argspec = inspect.getargspec(cb)
                        count = len(argspec.args)
                        if hasattr(cb, 'im_self'): count -= 1

                        if count == 2: 
                            BigWorld.callback(0, lambda: cb(0, data))
                        elif count == 1: 
                            BigWorld.callback(0, lambda: cb(data))
                        else:
                            BigWorld.callback(0, lambda: cb(0, data, None))
                    except:
                        try: BigWorld.callback(0, lambda: cb(0, data))
                        except: pass

                def makeMock(obj_name, method_name):
                    def force_cb(self, *args, **kwargs):
                        cb  = next((a for a in args if callable(a)), kwargs.get('callback'))
                        req = args[0] if len(args) > 0 else None
                        res = 0

                        if method_name in ('get', 'getCache', 'request'):
                            if obj_name == 'stats':
                                res = off_stats.get(req, 0)
                            else:
                                res = off_stats.get(req, {})

                        elif method_name == 'getItems':
                            if obj_name == 'inventory':
                                if req == 1:
                                    res = {
                                        'compDescr': inv_vehicles,
                                        'crew': crew_map,
                                        'shells': dict((invID, []) for invID in my_garage),
                                        'shellsLayout': dict((invID, {}) for invID in my_garage),
                                        'repair': dict((invID, (0, 100)) for invID in my_garage),
                                        'eqs': dict((invID, [0, 0, 0]) for invID in my_garage),
                                        'eqsLayout': dict((invID, [0, 0, 0]) for invID in my_garage),
                                        'settings': dict((invID, 0) for invID in my_garage),
                                        'lock': dict((invID, 0) for invID in my_garage)
                                    }
                                elif req == 8:
                                    res = {
                                        'compDescr': t_cache,
                                        'vehicle': t_in_veh
                                    }
                                elif req in _modules_by_type:
                                    res = _modules_by_type[req]
                                else:
                                    res = {}
                            elif obj_name == 'shop':
                                nationID = args[1] if len(args) > 1 else None
                                if req == 1:
                                    res_shop = {}
                                    for name in tank_list:
                                        try:
                                            nID, vID = vehicles.g_list.getIDsByName(name)
                                            if nID == nationID:
                                                res_shop[vID] = (150000, 0)
                                        except: pass
                                    res = (res_shop, set())
                                elif req in _modules_by_type:
                                    res_shop = {}
                                    for cd in _modules_by_type[req].keys():
                                        res_shop[cd] = (1000, 0)
                                    res = (res_shop, set())
                                elif req == 10:
                                    res_shop = {}
                                    if nationID is not None and nationID < len(nations.NAMES):
                                        for shellID in vehicles.g_cache.shellIDs(nationID).values():
                                            cd = vehicles.makeIntCompactDescrByID('shell', nationID, shellID)
                                            res_shop[cd] = (100, 0)
                                    res = (res_shop, set())
                                elif method_name == 'getSellPriceModifiers':
                                    res = (1.0, 1.0)
                                elif method_name == 'getPaidRemovalCost':
                                    res = 10
                                elif method_name == 'getTradeFees':
                                    res = {}
                                elif method_name == 'getVehiclesSellPrices':
                                    res = {}
                                else:
                                    res = ({}, set())
                        elif method_name == 'setCurrentVehicle':
                            invID = args[0] if args else None
                            if invID is not None and invID in veh_cds:
                                import CurrentVehicle
                                CurrentVehicle.g_currentVehicle._CurrentVehicle__vehicle = OfflineVehicleWrapper(invID)
                                off_stats['currentVehInvID'] = invID
                                BigWorld.callback(0.05, CurrentVehicle.g_currentVehicle.onChanged)
                            res = 0
                        elif obj_name == 'shop':
                                if method_name == 'getBerthsPrices':
                                    res = (300, [300, 600, 900])
                                elif method_name == 'getTankmanCost':
                                    res = ((0, 0), (20000, 0), (0, 200))
                                elif method_name == 'getSlotsPrices':
                                    res = (300, [300, 600, 900])
                                elif method_name == 'getExchangeRate':
                                    res = (400, 1)
                                elif method_name == 'getFreeXPConversion':
                                    res = (5, 1)
                                elif method_name == 'getPremiumCost':
                                    res = {1: 250, 3: 650, 7: 1200}
                        call_smart(cb, res)
                    return force_cb

                mocked_methods = [
                    'request', 'get', 'getItems', 'getCache',
                    'setCurrentVehicle', 'changeVehicleSetting', 'respecTankman',
                    'equipTankman', 'buyTankman', 'addTankmanSkill', 'dropTankmanSkill',
                    'getVehicleSellPrice', 'getComponentSellPrice', 'buyVehicle', 'buy',
                    'sell', 'repair', 'exchange', 'convertToFreeXP', 'upgradeToPremium',
                    'buySlot', 'buyBerths',
                    'getBerthsPrices', 'getTankmanCost', 'getSlotsPrices',
                    'getExchangeRate', 'getFreeXPConversion', 'getPremiumCost',
                    'getSellPriceModifiers', 'getPaidRemovalCost', 'getTradeFees',
                    'getVehiclesSellPrices', 'getPassportChangeCost', 'getPrice',
                    'getBerthsPrices', 'getNextBerthPackPrice',
                ]

                for s in ['inventory', 'stats', 'shop', 'dossierCache']:
                    obj = getattr(p, s, None)
                    if obj:
                        for m in mocked_methods:
                            setattr(obj, m, new.instancemethod(makeMock(s, m), obj, obj.__class__))
                        if s == 'shop':
                            def get_next_berth_price(berths, berths_prices):
                                return 300
                            obj.getNextBerthPackPrice = get_next_berth_price

                inv_obj = getattr(p, 'inventory', None)
                if inv_obj:
                    def fake_equip(self, vehicleInvID, itemCompDescr, callback=None):
                        try:
                            from CurrentVehicle import g_currentVehicle
                            veh = g_currentVehicle.vehicle
                            if veh and veh.descriptor:
                                veh.descriptor.installComponent(itemCompDescr)
                                new_cd = veh.descriptor.makeCompactDescr()
                                veh_cds[vehicleInvID]    = new_cd
                                inv_vehicles[vehicleInvID] = new_cd
                        except Exception as e:
                            print "[OFFLINE] equip error: %s" % e
                        if callback:
                            BigWorld.callback(0.01, lambda: callback(0))

                    def fake_equipTurret(self, vehicleInvID, itemCompDescr, slotIdx, callback=None):
                        try:
                            from CurrentVehicle import g_currentVehicle
                            veh = g_currentVehicle.vehicle
                            if veh and veh.descriptor:
                                veh.descriptor.installTurret(itemCompDescr, slotIdx)
                                new_cd = veh.descriptor.makeCompactDescr()
                                veh_cds[vehicleInvID]    = new_cd
                                inv_vehicles[vehicleInvID] = new_cd
                        except Exception as e:
                            print "[OFFLINE] equipTurret error: %s" % e
                        if callback:
                            BigWorld.callback(0.01, lambda: callback(0))

                    inv_obj.equip       = new.instancemethod(fake_equip,       inv_obj, inv_obj.__class__)
                    inv_obj.equipTurret = new.instancemethod(fake_equipTurret, inv_obj, inv_obj.__class__)

                p.selectVehicle = lambda invID: (
                    setattr(CurrentVehicle.g_currentVehicle, '_CurrentVehicle__vehicle', OfflineVehicleWrapper(invID)),
                    CurrentVehicle.g_currentVehicle.onChanged(),
                    None
                )[2]

                p.stats._Stats__cache = off_stats
                p.inventory._Inventory__cache = {
                    'items':        dict((cd, 1) for cd in _modules_inventory.keys()),
                    'compDescr':    inv_vehicles,
                    'vehicles':     { 'invData': inv_data },
                    'tankmen':      t_cache,
                    'potapovQuests': {}
                }

                class FakeS(str):
                    def __getattr__(self, n): return lambda *a, **k: FakeS("")
                    def __getitem__(self, k): return FakeS("")
                AS.AccountSettings._AccountSettings__readUserSection = staticmethod(lambda *a: FakeS(""))

                if 1 in veh_cds:
                    CurrentVehicle.g_currentVehicle._CurrentVehicle__vehicle = OfflineVehicleWrapper(1)

            from gui.WindowsManager import g_windowsManager
            g_windowsManager.showLobby()

            try:
                from gui.Scaleform.Waiting import Waiting
                Waiting.close()
            except: pass

            def refresh_gui():
                g_playerEvents.onStatsResync()
                g_playerEvents.onInventoryResync()
                from gui.WindowsManager import g_windowsManager
                g_windowsManager.showLobby() 

            BigWorld.callback(1.5, refresh_gui)

        except Exception:
            traceback.print_exc()

    connectionManager.connect = fake_connect
    print "[OFFLINE] Ready"
init_offline()
def _apply_surgical_fixes():
    from gui.Scaleform.utils.gui_items import FittingItem
    def safe_level_fget(self):
        try:
            if self.itemTypeName == 'vehicle':
                return self.descriptor.level
            return self.descriptor.get('level', 0)
        except:
            return 0
    FittingItem.level = property(safe_level_fget)
    def safe_name_fget(self):
        try:
            if self.itemTypeName == 'vehicle':
                return self.descriptor.type.userString
            return self.descriptor.get('userString', 'Unknown Item')
        except:
            return "Item %s" % str(getattr(self, 'compactDescr', 'ID'))
    FittingItem.name = property(safe_name_fget)

_apply_surgical_fixes()