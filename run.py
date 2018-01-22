import os

# use the upper one when coding, use lower one when testing and competing
# import battlecode.python.battlecode as bc
import battlecode as bc

import random
import sys
import traceback
from enum import Enum
print("current path:\n"+os.getcwd())
print("testing new player")

class Strategy:   
    Develop, Regular, Blitz, Retreat, Surround, Defense = range(0, 6)

knownEnemyLoc = []
knownEnemyLocLimit = 30
knownEnemyLocRefreshRate = 0.5

resourceLoc = []

knownEnemyStrcutureLoc = []

ranger_Engage_Option = False
rangerSafeAddtionalDistance = 15

def stat():
    # first we figure out how many unit of each type we currently have
    n_worker = 0
    n_factory = 0
    n_knight = 0
    n_ranger = 0
    n_mage = 0 
    n_healer =0
    for unit in gc.my_units():
        if unit.unit_type == bc.UnitType.Factory:
            n_factory += 1
        elif unit.unit_type == bc.UnitType.Worker:
            n_worker += 1
        elif unit.unit_type == bc.UnitType.Knight:
            n_knight += 1
        elif unit.unit_type == bc.UnitType.Ranger:
            n_ranger += 1
        elif unit.unit_type == bc.UnitType.Mage:
            n_mage += 1
        elif unit.unit_type == bc.UnitType.Healer:
            n_healer += 1
    return n_worker,n_factory,n_knight,n_ranger,n_mage,n_healer
    
def decideProduction(n_ranger, n_mage, n_healer, n_knight, strategy):
    if(strategy == 0):
        return bc.UnitType.Ranger
        
    total = n_ranger + n_mage + n_healer + n_knight
    diff_ranger = n_ranger / total - 0.4
    diff_mage = n_mage / total - 0.2
    diff_knight = n_kight / total - 0.3
    diff_healer = n_healer / total - 0.1
    
    if(min(diff_ranger,diff_mage,diff_healer, diff_knight) == diff_ranger):
        return bc.UnitType.Ranger
    elif(min(diff_ranger,diff_mage,diff_healer, diff_knight) == diff_knight):
        return b.UnitType.Knight
    elif(min(diff_ranger,diff_mage,diff_healer, diff_knight) == diff_mage):
        return bc.UnitType.Mage
    elif(min(diff_ranger,diff_mage,diff_healer, diff_knight) == diff_healer):
        return bc.UnitType.Healer

def get_enemy(myteam):
    if myteam == bc.Team.Red:
        return bc.Team.Blue
    else:
        return bc.Team.Red
        
def getRandomLocation():
    return random.choice(directions)

def updateKnownEnemyLocations(enemyLoc):
    if(len(knownEnemyLoc) <= knownEnemyLocLimit):
        knownEnemyLoc.append(enemyLoc)
        return
    if(random.random() < knownEnemyLocRefreshRate):
        indexToUse = random.randint(0,knownEnemyLocLimit)
        knownEnemyLoc.pop(indexToUse)
        knownEnemyLoc.insert(indexToUse, enemyLoc)
        return

def getDirToTargetMapLocGreedy(ourUnit, tarLoc):
    dirToTar = ourUnit.location.map_location().direction_to(tarLoc)
    if (dirToTar == Direction.center):
        return dirToTar
    i = 0
    while(i < len(directions)):
        newLoc = directions[i]
        if(gc.can_move(ourUnit.id, newLoc)):
            return newLoc
    return Direction.center  
        
def getDirAwayTargetMapLocGreedy(gc, ourUnit, tarLoc):
    dirToTar = tarLoc.direction_to(ourUnit.location.map_location());
    if (dirToTar == Direction.center):
        return dirToTar
    i = 0
    while(i < len(directions)):
        newLoc = directions[i]
        if(gc.can_move(ourUnit.id, newLoc)):
            return newLoc
    return Direction.center

def findNearestLocation(ourLoc, otherLocs):
    minDist = 999999999
    neaerestLoc = ourLoc
    for loc in otherLocs:
        dist = ourLoc.distance_squared_to(loc)
        if dist < minDist:
            minDist = dist
            nearestLoc = otherLoc
    return nearestLoc
    
def getShuffledIndex(size):
    i = 0
    temp = []
    while(i < size):
        temp.append(i)
        i = i + 1
    random.shuffle(temp)
    return temp
    
def clearDuplicates(l):
    seen = set()
    seen2 = set()
    seenAdd = seen.add
    seen2Add = seen2.add
    for item in l:
        if(item in seen):
            seen2Add(item)
        else:
            seenAdd(item)
    return list(seen2)
    
def updateKnownReourceLocations(resLoc):
    resourceLoc.append(resLoc)
    resourceLoc = clearDuplicates(resourceLoc)
    
def getANearbyResourceLocation(worker):
    checkRadius = worker.vision_range
    nearbyLocs = gc.all_locations_within(worker.location.map_location(),checkRadius)
    for resLoc in nearbyLocs:
        if(gc.karbonite_at(resLoc) > 0):
            updateKnownReourceLocations(resLoc)
    if(len(resourceLoc) > 0):
        return random.choice(resourceLoc)
    else:
        return None
        
def findFriendToHeal(gc, healer, friendsInHealRange):
    maploc = healer.location.map_location()
    unitToHeal = None
    maxHPLoss = -9999
    for unit in friendsInHealRange:
        HPLoss = unit.max_health() - unit.health()
        if(HPLoss > maxHPLoss):
            maxHPLoss = HPLoss
            unitToHeal = unit
    return unit
    
def findNearestUnitJavelinInRange(knight, units):
    nearestUnit = units[0]
    minDistance = 999999999
    ourMapLocation = knight.location.map_location()
    for unit in units:
        otherLocation = unit.location.map_location()
        distanceSqr = ourMapLocation.distance_squared_to(otherLocation)
        if distanceSqr < minDistance:
            continue
        if distanceSqr <= knight.ability_range():
            minDistance = distanceSqr
            nearestUnit = unit
    return nearestUnit
        
def getUnitsNeedHeal(units):
    unitsInHelp = []
    for unit in units:
        if((unit.health / unit.max_health < 0.5) and (unit.unit_type != bc.UnitType.Factory) and (unit.unit_type != bc.UnitType.Rocket)) :
            unitsInHelp.append(unit)
    return unitsInHelp
    
def getUnitsNeedRepair(units):
    unitsNeedRepair = []
    for unit in units:
        if(((unit.health / unit.max_health) < 0.5 ) and (unit.unit_type == bc.UnitType.Factory)) :
            unitsNeedRepair.append(unit)
    return unitsNeedRepair
    
def blueprintFactoryNearby(gc, uid):
    d = Direction.Center
    for dir in directions:
        if(gc.can_blueprint(uid, bc.UnitType.Factory, dir)):
            gc.blueprint(uid, bc.UnitType.Factory, dir)
            return True
    return False
    
def blueprintRocketNearby(gc, worker):
    uid = worker.id
    dir = Direction.Center
    for dir in directions:
        if(gc.can_blueprint(uid, bc.UnitType.Rocket, dir)):
            gc.blueprint(uid, bc.UnitType.Rocket, dir)
            return True
    return False
    
def harvestNearby(gc, worker):
    uid = worker.id
    dir = Direction.Center
    for dir in directions:
        if(gc.can_harvest(uid, dir)):
            gc.harvest(uid, dir)
            return True
    return False
    
def replicateNearby(gc, worker):
    uid = worker.id
    dir = Direction.Center
    for dir in directions:
        if(gc.can_replicate(uid, dir)):
            gc.replicate(uid, dir)
            return True
    return False
    
def getEnemyStructure(units):
    targetStructures = []
    for unit in units:
        if((unit.unit_type == bc.UnitType.Factory) and (unit.unit_type == bc.UnitType.Rocket)) :
            targetStructures.append(unit)
    return targetStructures
    
def getStructureToSnipe(ranger, units):
    struc = random.choice(getEnemyStructure(unit))
    while(struc.location.map_location().distance_squared_to(ranger.location.map_location()) > ranger.ability_range()):
        struc = random.choice(getEnemyStructure(unit))
    return struc
    
def findNearestUnit(ourMapLocation,units):
    nearestUnit = units[0]
    minDistance = 999999999
    for unit in units:
        otherLocation = unit.location.map_location()
        distanceSqr = ourMapLocation.distance_squared_to(otherLocation)
        if distanceSqr < minDistance:
            minDistance = distanceSqr
            nearestUnit = unit
    return nearestUnit

def findNearestUnit_Ranger(ranger, enemies):
    ourMapLoc = ranger.location.map_location()
    nearestUnit = enemies[0]
    minDistance = 999999999
    for unit in enemies:
        otherLoc = unit.location.map_location()
        distanceSqr = ourMapLoc.distance_squared_to(otherLoc)
        if(distanceSqr < minDistance and gc.can_attack(ranger.id, unit.id)):
            minDistance = distanceSqr
            nearestUnit = unit
    return nearestUnit
    
def findNearestUnit_Mage(mage, enemies):
    ourMapLoc = mage.location.map_location()
    nearestUnit = enemies[0]
    minDistance = 999999999
    for unit in enemies:
        otherLoc = unit.location.map_location()
        distanceSqr = ourMapLoc.distance_squared_to(otherLoc)
        if(distanceSqr < minDistance and gc.can_attack(mage.id, unit.id)):
            minDistance = distanceSqr
            nearestUnit = unit
    return nearestUnit
    
def findNearestUnitInRangerAttackRange(ranger, units):
    nearestUnit = units[0]
    minDistance = 999999999
    ourMapLocation = ranger.location.map_location()
    for unit in units:
        otherLocation = unit.location.map_location()
        distanceSqr = ourMapLocation.distance_squared_to(otherLocation)
        if distanceSqr < minDistance:
            continue
        if distanceSqr <= ranger.ranger_cannot_attack_range():
            minDistance = distanceSqr
            nearestUnit = unit
    return nearestUnit

gc = bc.GameController()
directions = list(bc.Direction)

# It's a good idea to try to keep your bots deterministic, to make debugging easier.
# determinism isn't required, but it means that the same things will happen in every thing you run,
# aside from turns taking slightly different amounts of time due to noise.
random.seed(6137)

#Reaserch Queue
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Ranger)
gc.queue_research(bc.UnitType.Knight)
gc.queue_research(bc.UnitType.Rocket)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Knight)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Knight)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Mage)
gc.queue_research(bc.UnitType.Worker)
gc.queue_research(bc.UnitType.Mage)
gc.queue_research(bc.UnitType.Mage)

my_team = gc.team()
enemy_team = get_enemy(my_team)

worker_max = 8
worker_min = 1
factory_max = 6

####################### HELPERS ########################

# A GameController is the main type that you talk to the game with.
# Its constructor will connect to a running game.
print("pystarted")

while True:
    # FOR EACH ROUND OF THE GAME
    # We only support Python 3, which means brackets around print()
    print('pyround:', gc.round())

    n_worker,n_factory,n_knight,n_ranger,n_mage,n_healer = stat()
    
    if(gc.round() < 100):
        strat = Strategy.Develop
    if(gc.round() > 50 and gc.round() < 100 and n_ranger > 5):
        strat = Strategy.Blitz
    # now actual unit logics
    # frequent try/catches are a good idea
    try:
        # walk through our units:
        for unit in gc.my_units():
            move_found = False
            #FACTORY LOGIC ###########################
            # simply unload anything and then produce knight if possible
            if unit.unit_type == bc.UnitType.Factory:
                unitPro = decideProduction(n_ranger, n_mage, n_healer, n_knight, strat)
                garrison = unit.structure_garrison()
                if len(garrison) > 0:
                    for d in directions:
                        if gc.can_unload(unit.id, d):
                            gc.unload(unit.id, d)
                            move_found = True
                            break
                elif n_worker<worker_min and gc.can_produce_robot(unit.id, bc.UnitType.Worker):
                    gc.produce_robot(unit.id, bc.UnitType.Worker)
                    move_found = True
                elif gc.can_produce_robot(unit.id, unitPro):
                    gc.produce_robot(unit.id, unitPro)
                    move_found = True 
                if move_found:
                    continue

            # WORKER LOGIC ###########################
            elif unit.unit_type == bc.UnitType.Worker:
                location = unit.location
                enemies = gc.sense_nearby_units_by_team(location.map_location(), unit.vision_range,enemy_team)
                if(len(enemies) > 0):
                    updateKnownEnemyLocations(enemies[0].location.map_location())
                    
                if location.is_on_map():
                    ## first, let's look for nearby blueprints to work on
                    nearby = gc.sense_nearby_units(location.map_location(), unit.vision_range)
                    for other in nearby:
                        if gc.can_build(unit.id, other.id):
                            gc.build(unit.id, other.id)
                            move_found = True
                            break
                    if move_found:
                        continue

                    ## nothing to keep building, then see if should build factory
                    # pick a random direction:
                    d = random.choice(directions)
                    #try to build a factory if we need more factories:
                    if gc.karbonite() > bc.UnitType.Factory.blueprint_cost() and gc.can_blueprint(unit.id, bc.UnitType.Factory, d) and n_factory<5:
                        gc.blueprint(unit.id, bc.UnitType.Factory, d)
                        move_found = True

                    if move_found:
                        continue

                    d = random.choice(directions)
                    if n_worker<worker_max and gc.can_replicate(unit.id,d):
                        gc.replicate(unit.id,d)
                        move_found = True

                    if move_found:
                        continue

                    ## now check if there are karbonite to harvest.
                    for d in directions:
                        if gc.can_harvest(unit.id,d):
                            gc.harvest(unit.id,d)
                            #TODO need more systematic harvesting according to map info
                            # print("harvest success!!!!!!!!!!!!!")
                            move_found = True
                            break
                    if move_found:
                        continue

                    ## and if nothing to harvest, then move
                    d = random.choice(directions)
                    if gc.is_move_ready(unit.id) and gc.can_move(unit.id, d):
                        gc.move_robot(unit.id, d)
                        move_found = True
                    if move_found:
                        continue

            # KNIGHT LOGIC #####################################
            elif unit.unit_type == bc.UnitType.Knight:
                knight_moved = False
                location = unit.location
                enemies = gc.sense_nearby_units_by_team(location.map_location(), unit.vision_range,enemy_team)
                if(len(enemies) > 0):
                    updateKnownEnemyLocations(enemies[0].location.map_location())
                    
                if(location.is_on_map()):
                    ourMapLoc = location.map_location()
                    ## first, let's look for enemies in vision (not usre if -1 works?)
                    # 50 is the sense range of knight
                    enemies = gc.sense_nearby_units_by_team(location.map_location(),50,enemy_team)
                    if(len(enemies)>0):
                        nearestEnemy = findNearestUnit(ourMapLoc,enemies)
                        enemyToJave = findNearestUnitJavelinInRange(unit, enemies)
                        dirToNearestEnemy = ourMapLoc.direction_to(nearestEnemy.location.map_location())
                        if(gc.is_javelin_ready(unit.id) and gc.can_javelin(unit.id, enemyToJave.id)):
                            gc.javelin(unit.id, enemyToJave.id)
                        if(gc.is_move_ready(unit.id) and gc.can_move(unit.id, dirToNearestEnemy)):
                            gc.move_robot(unit.id, dirToNearestEnemy)
                        if(gc.is_attack_ready(unit.id)  and gc.can_attack(unit.id,nearestEnemy.id)):
                            gc.attack(unit.id, nearestEnemy.id)
                            
                    if (gc.is_move_ready(unit.id)): # if didn't move to an enemy, then move randomly
                        d = random.choice(directions)
                        if (gc.can_move(unit.id, d)):
                            gc.move_robot(unit.id, d)

            # Ranger LOGIC #####################################
            elif (unit.unit_type == bc.UnitType.Ranger):
                location = unit.location
                enemies = gc.sense_nearby_units_by_team(location.map_location(), unit.vision_range,enemy_team)
                if(len(enemies) > 0):
                    updateKnownEnemyLocations(enemies[0].location.map_location())
                    
                if(location.is_on_map()):
                    ourMapLoc = location.map_location()
                    enemies = gc.sense_nearby_units_by_team(location.map_location(),50,enemy_team)
                    if(len(enemies) > 0 and (gc.is_attack_ready(unit.id) or gc.is_begin_snipe_ready(unit.id))):
                        targetUnit = findNearestUnitInRangerAttackRange(unit, enemies)
                        targetStructures = getEnemyStructure(enemies)
                        if len(targetStructures) > 0:
                          targetStructureLoc = targetStructures[0].location
                          if((gc.is_begin_snipe_ready(unit.id)) and (gc.can_begin_snipe(unit.id, targetStructureLoc))):
                              gc.begin_snipe(unit.id, targetStructureLoc)
                        if((gc.is_attack_ready(unit.id)) and (gc.can_attack(unit.id, targetUnit.id))and(not unit.ranger_is_sniping())):
                            gc.attack(unit.id, targetUnit.id)
                            
                    if(len(enemies) > 0 and gc.is_move_ready(unit.id)):
                        if((!gc.is_attack_ready(unit.id)) and (!gc.is_begin_snipe_ready(unit.id))):
                            nearestEnemy = findNearestUnit(ourMapLoc, enemies)
                            moveDir = getDirAwayTargetMapLocGreedy(gc, unit, nearestEnemy.location.map_location())
                            if(gc.can_move(unit.id, moveDir)):
                                gc.move_robot(unit.id, moveDir)
                        else:
                            nearestEnemy = findNearestUnit(ourMapLoc, enemies)
                            dist = unit.location.map_location().distance_squared_to(nearestEnemy.location.map_location())
                            if(ranger_Engage_Option == True):
                                if(dist < unit.ranger_cannot_attack_range()):
                                    moveDir = getDirAwayTargetMapLocGreedy(gc, unit, nearestEnemy.location.map_location())
                                else:
                                    moveDir = getDirToTargetMapLocGreedy(gc, unit, nearestEnemy.location.map_location())
                            else:
                                safeDist = unit.attack_range() + rangerSafeAddtionalDistance
                                if(dist < safeDist):
                                    moveDir = getDirAwayTargetMapLocGreedy(gc, unit, nearestEnemy.location.map_location())
                                else:
                                    moveDir = getDirToTargetMapLocGreedy(gc, unit, nearestEnemy.location.map_location())
                            
                            if(gc.can_move(unit.id, moveDir)):
                                gc.move_robot(unit.id, moveDir)
                            
            # Mage LOGIC #####################################
            elif unit.unit_type == bc.UnitType.Mage:
                knight_moved = False
                location = unit.location
                enemies = gc.sense_nearby_units_by_team(location.map_location(), unit.vision_range,enemy_team)
                if(len(enemies) > 0):
                    updateKnownEnemyLocations(enemies[0].location.map_location())
                    
                if location.is_on_map():
                    ourMapLoc = location.map_location()
                    if len(enemies)>0:
                        nearestEnemy = findNearestUnit(ourMapLoc,enemies)
                        dirToNearestEnemy = ourMapLoc.direction_to(nearestEnemy.location.map_location())
                        if gc.is_blink_ready(unit.id) and gc.can_blink(unit.id, nearestEnemy.location.map_location()):
                            gc.blink(unit.id, nearestEnemy.location.map_location())
                        if gc.is_attack_ready(unit.id)  and gc.can_attack(unit.id,nearestEnemy.id):
                            gc.attack(unit.id, nearestEnemy.id)
                    if gc.is_move_ready(unit.id): # if didn't move to an enemy, then move randomly
                        d = random.choice(directions)
                        if gc.can_move(unit.id, d):
                            gc.move_robot(unit.id, d)

            # HEALER LOGIC #####################################
            elif (unit.unit_type == bc.UnitType.Healer):
                location = unit.location
                enemies = gc.sense_nearby_units_by_team(location.map_location(), unit.vision_range,enemy_team)
                if(len(enemies) > 0):
                    updateKnownEnemyLocations(enemies[0].location.map_location())
                
                if(location.is_on_map()):
                    ourMapLoc = location.map_location()
                    unitsInHelp = getUnitsNeedHeal(gc.my_units())
                    if (len(unitsInHelp) > 0):
                        nearestInHelp = findFriendToHeal(gc, unit, unitsInHelp)
                        dirToNearestInHelp = ourMapLoc.direction_to(nearestInHelp.location.map_location())
                        if(gc.is_move_ready(unit.id) and gc.can_move(unit.id, dirToNearestInHelp)):
                            gc.move_robot(unit.id, nearestInHelp)
                        if(gc.is_heal_ready(unit.id) and gc.can_heal(unit.id,nearestInHelp.id)):
                            gc.heal(unit.id, nearestInHelp.id)
                            
                    if (gc.is_move_ready(unit.id)): # if didn't move to an enemy, then move randomly
                        # qiuqiu: unitsInHelp may be empty
                        if len(unitsInHelp) > 0:
                            c = random.choice(unitsInHelp)
                            d = getDirToTargetMapLocGreedy(gc, unit, c)
                            if (gc.can_move(unit.id, d)):
                                gc.move_robot(unit.id, d)
                        else:
                            if gc.is_move_ready(unit.id): # if didn't move to an enemy, then move randomly
                                d = random.choice(directions)
                            if gc.can_move(unit.id, d):
                                gc.move_robot(unit.id, d)

    except Exception as e:
        print('Error:', e)
        # use this to show where the error was
        traceback.print_exc()

    # send the actions we've performed, and wait for our next turn.
    gc.next_turn()

    # these lines are not strictly necessary, but it helps make the logs make more sense.
    # it forces everything we've written this turn to be written to the manager.
    sys.stdout.flush()
    sys.stderr.flush()