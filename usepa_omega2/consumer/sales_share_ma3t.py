import numpy as np
import math
from pathlib import Path

def PHEVT_Consumer():
    path_code = Path(__file__).parent
    path_project = Path(path_code).parent.parent
    path_inputs = path_project / 'input_samples' / 'ma3t' # ToDo: Getting the inputs from the templates directory is temporary for testing
    path_outputs = path_project / 'output'
    YearOnMarket = np.loadtxt(path_inputs / 'tech_yearonmarket_templatev001.csv', delimiter=',', skiprows=1, usecols=range(5,6))
    dBeta = np.loadtxt(path_inputs / 'consumer_beta_templatev001.csv', delimiter=',', skiprows=0, usecols=range(1,136))
    bDummyFlag = np.transpose(np.loadtxt(path_inputs / 'tech_nestheterogeneity_templatev001.csv', delimiter=',', skiprows=1, usecols=range(5,10)))
    choiceNames = np.loadtxt(path_inputs / 'tech_choicenames_templatev001.csv', delimiter=',', skiprows=0, usecols=range(1, 406), dtype=str)
    generalizedcost = np.loadtxt(path_inputs / 'generalizedcosts_templatev001.csv', delimiter=',', skiprows=1, usecols=range(1,47))
    # generalizedcostchoicenames = np.loadtxt(path_inputs + 'generalizedcosts.csv', delimiter=',', skiprows=1, usecols=range(0, 1), dtype=str)
    iNestLayerNum = 5
    iLastNestLayerIdx = iNestLayerNum - 1
    iNestPerNestNum = [5, 3, 3, 3, 3]
    iChoiceNum = [5, 15, 45, 135, 405]
    dExtremeHighPrice = 99999999
    iIndividualNum = [1]# Use a single aggregate consumer for now
    iGroupDimNum = 1 # Use a single aggregate consumer for now
    firstAnalysisYear = 2005
    lastAnalysisYear = 2050
    iStepNum = lastAnalysisYear - firstAnalysisYear + 1
    dProbNestLayer1 = [choiceNames[0,]] # dProbNestLayer1 = [list(range(0, 5))]
    dProbNestLayer2 = [choiceNames[1,]] # dProbNestLayer2 = [list(range(0, 14))]
    dProbNestLayer3 = [choiceNames[2,]] # dProbNestLayer3 = [list(range(0, 40))]
    dProbNestLayer4 = [choiceNames[3,]] # dProbNestLayer4 = [list(range(0, 100))]
    dProbNestLayer5 = [choiceNames[4,]] # dProbNestLayer5 = [generalizedcostchoicenames]
    choiceProb = np.zeros([iChoiceNum[iLastNestLayerIdx], ])
    choiceGeneralizedCost = np.zeros([iChoiceNum[iLastNestLayerIdx], ])
    #choiceProbAllYears = np.vstack((choiceNames[0,], choiceNames[1,], choiceNames[2,], choiceNames[3,], choiceNames[4,]))
    choiceProbAllYears =['Nest1', 'Nest2', 'Nest3', 'Nest4', 'Nest5', 'Year', 'ChoiceProb', 'GeneralizedCost']

    for iStepIndex in range(0, iStepNum):
        #Calculate choice probability of each technology by each consumer---objConsumer(iConsumer).ChoiceProb(iChoice)
        dCost = np.zeros([iNestLayerNum, iChoiceNum[iLastNestLayerIdx]])
        dEtoU = np.zeros([iNestLayerNum, iChoiceNum[iLastNestLayerIdx]])
        dSumEtoU = np.zeros([iNestLayerNum, iChoiceNum[iLastNestLayerIdx - 1]])
        dProb = np.zeros([iNestLayerNum, iChoiceNum[iLastNestLayerIdx]])

        for iConsumer in range(0, iIndividualNum[iGroupDimNum - 1]):
            #1
            AssignValueToArray(dSumEtoU, 0, iLastNestLayerIdx, 0, iChoiceNum[iLastNestLayerIdx - 1], 0)
            iRealChoice = 0
            for iChoice in range(0, iChoiceNum[iLastNestLayerIdx]):
                if bDummyFlag[iLastNestLayerIdx, iChoice] == 0:
                    dCost[iLastNestLayerIdx, iChoice] = dExtremeHighPrice
                    dEtoU[iLastNestLayerIdx, iChoice] = 0
                else:
                    # if YearOnMarket[iRealChoice] <= iStepIndex + firstAnalysisYear:
                    if YearOnMarket[iChoice] <= iStepIndex + firstAnalysisYear:
                        dCost[iLastNestLayerIdx, iChoice] = generalizedcost[iRealChoice, iStepIndex]
                    else:
                        dCost[iLastNestLayerIdx, iChoice] = dExtremeHighPrice
                    #calculate dCost(iNestLayerNum, i)
                    #function of dLamda, and attributes; form depends on attributes and parameters setting
                    #iTemp = math.trunc((iChoice - 1) / iNestPerNestNum[iLastNestLayerIdx]) + 1
                    iTemp = math.trunc((iChoice) / iNestPerNestNum[iLastNestLayerIdx])
                    dEtoU[iLastNestLayerIdx, iChoice] = math.exp(dBeta[iLastNestLayerIdx, iTemp] * dCost[iLastNestLayerIdx, iChoice])
                    #calculate dSumEtoU(iNestLayerNum, i)
                    dSumEtoU[iLastNestLayerIdx, iTemp] = dSumEtoU[iLastNestLayerIdx, iTemp] + dEtoU[iLastNestLayerIdx, iChoice]
                    iRealChoice = iRealChoice + 1
            #calculate dProb(iNestLayerNum, i)
            for iChoice in range(0, iChoiceNum[iLastNestLayerIdx]):
                #iTemp = math.trunc((iChoice - 1) / iNestPerNestNum[iLastNestLayerIdx]) + 1
                iTemp = math.trunc((iChoice) / iNestPerNestNum[iLastNestLayerIdx])
                if bDummyFlag[iLastNestLayerIdx, iChoice] == 0:
                    dProb[iLastNestLayerIdx, iChoice] = 0
                elif bDummyFlag[iLastNestLayerIdx, iChoice] == 100:
                    dProb[iLastNestLayerIdx, iChoice] = 1
                elif dSumEtoU[iLastNestLayerIdx, iTemp] == 0:
                    dTemp = 0
                    for iTemp2 in range(0, iNestPerNestNum[iLastNestLayerIdx]):
                        # dTemp = dTemp + bDummyFlag[iLastNestLayerIdx, (iTemp - 1) * iNestPerNestNum[iLastNestLayerIdx] + iTemp2]
                        dTemp = dTemp + bDummyFlag[iLastNestLayerIdx, iTemp * iNestPerNestNum[iLastNestLayerIdx] + iTemp2]
                    dProb[iLastNestLayerIdx, iChoice] = 1 / dTemp / 11
                else:
                    dProb[iLastNestLayerIdx, iChoice] = dEtoU[iLastNestLayerIdx, iChoice] / dSumEtoU[iLastNestLayerIdx, iTemp]
            for iLayer in range((iLastNestLayerIdx - 1), -1, - 1):
                #2
                for iNest in range(0, iChoiceNum[iLayer]):
                    #3
                    if bDummyFlag[iLayer, iNest] == 0 or dSumEtoU[iLayer + 1, iNest] == 0:
                        dCost[iLayer, iNest] = dExtremeHighPrice
                        dEtoU[iLayer, iNest] = 0
                    else:
                        #calculate dCost(iLayer, iNest)
                        try:
                            dCost[iLayer, iNest] = math.log(dSumEtoU[iLayer + 1, iNest]) / dBeta[iLayer + 1, iNest]
                        except:
                            dCost = 0
                        #calculate dEtoU(iLayer, iNest)
                        #iTemp = math.trunc((iNest - 1) / iNestPerNestNum[iLayer]) + 1
                        iTemp = math.trunc((iNest) / iNestPerNestNum[iLayer])
                        dEtoU[iLayer, iNest] = math.exp(dBeta[iLayer, iTemp] * dCost[iLayer, iNest])
                        #calculate dSumEtoU(iNestLayerNum, i)
                        dSumEtoU[iLayer, iTemp] = dSumEtoU[iLayer, iTemp] + dEtoU[iLayer, iNest]
                    #3
                #calculate dProb(iLayer, iNest)
                for iNest in range(0, iChoiceNum[iLayer]):
                    #iTemp = math.trunc((iNest - 1) / iNestPerNestNum[iLayer]) + 1
                    iTemp = math.trunc((iNest) / iNestPerNestNum[iLayer])
                    if bDummyFlag[iLayer, iNest] == 0:
                        dProb[iLayer, iNest] = 0
                    elif bDummyFlag[iLayer, iNest] == 100:
                        dProb[iLayer, iNest] = 1
                    elif dSumEtoU[iLayer, iTemp] == 0:
                        dTemp = 0
                        for iTemp2 in range(0, iNestPerNestNum[iLayer]):
                            #dTemp = dTemp + bDummyFlag[iLayer, (iTemp - 1) * iNestPerNestNum[iLayer] + iTemp2]
                            dTemp = dTemp + bDummyFlag[iLayer, iTemp * iNestPerNestNum[iLayer] + iTemp2]
                        dProb[iLayer, iNest] = 1 / dTemp / 11
                    else:
                        dProb[iLayer, iNest] = dEtoU[iLayer, iNest] / dSumEtoU[iLayer, iTemp]
                #2
            #1

            iRealChoice = 0
            for iTemp in range(0, iChoiceNum[iLastNestLayerIdx]):
                if bDummyFlag[iLastNestLayerIdx, iTemp] > 0:
                    dTemp = 1
                    for iLayer in range(0, iNestLayerNum):
                        iNest = math.trunc(iTemp / (iChoiceNum[iLastNestLayerIdx] / iChoiceNum[iLayer]))
                        dTemp = dTemp * dProb[iLayer, iNest]
                    choiceProb[iTemp] = dTemp
                    choiceGeneralizedCost[iTemp] = generalizedcost[iRealChoice, iStepIndex]
                    iRealChoice = iRealChoice + 1

            # Output results
            dProbNestLayer1 = np.append(dProbNestLayer1, [dProb[0, ]], axis=0)
            # dProbNestLayer1 = np.append(dProbNestLayer1, [dProb[0, bDummyFlag[0,] != 0]], axis=0)
            dProbNestLayer2 = np.append(dProbNestLayer2, [dProb[1, ]], axis=0)
            # dProbNestLayer2 = np.append(dProbNestLayer2, [dProb[1, bDummyFlag[1,] != 0]], axis=0)
            dProbNestLayer3 = np.append(dProbNestLayer3, [dProb[2, ]], axis=0)
            # dProbNestLayer3 = np.append(dProbNestLayer3, [dProb[2, bDummyFlag[2,] != 0]], axis=0)
            dProbNestLayer4 = np.append(dProbNestLayer4, [dProb[3, ]], axis=0)
            # dProbNestLayer4 = np.append(dProbNestLayer4, [dProb[3, bDummyFlag[3,] != 0]], axis=0)
            dProbNestLayer5 = np.append(dProbNestLayer5, [dProb[4, ]], axis=0)
            # dProbNestLayer5 = np.append(dProbNestLayer5, [dProb[4, bDummyFlag[4,] != 0]], axis=0)
            choiceProbAllYears = np.vstack((choiceProbAllYears, np.transpose(np.append(choiceNames, np.append([(iStepIndex + firstAnalysisYear) * np.ones([iChoiceNum[iLastNestLayerIdx], ])], np.append([choiceProb], [choiceGeneralizedCost], axis=0), axis=0), axis=0))))
    np.savetxt(path_outputs / 'dProbNestLayer1.csv', np.transpose(dProbNestLayer1), delimiter=',', fmt='%s')
    np.savetxt(path_outputs / 'dProbNestLayer2.csv', np.transpose(dProbNestLayer2), delimiter=',', fmt='%s')
    np.savetxt(path_outputs / 'dProbNestLayer3.csv', np.transpose(dProbNestLayer3), delimiter=',', fmt='%s')
    np.savetxt(path_outputs / 'dProbNestLayer4.csv', np.transpose(dProbNestLayer4), delimiter=',', fmt='%s')
    np.savetxt(path_outputs / 'dProbNestLayer5.csv', np.transpose(dProbNestLayer5), delimiter=',', fmt='%s')
    np.savetxt(path_outputs / 'choiceProbAllYears.csv', choiceProbAllYears, delimiter=',', fmt='%s')

def AssignValueToArray(LcTargetArray, iLcRowL, iLcRowU, iLcColL, iLcColU, LcSourceArray):
    if isinstance(LcSourceArray, np.ndarray):
        # check dimensionality of target array. If 2 dim, then iLcDim=2. If 1 dim, then iLcDim=1
        iLcDim = LcTargetArray.ndim
        # check dimensionality of source array. If 2 dim, then iLcDimS=2. If 1 dim, then iLcDimS=1
        iLcDimS = LcSourceArray.ndim
        if iLcRowL == iLcRowU:
            if iLcDimS == 1:
                if iLcDim == 2:
                    for iLcCol in range(iLcColL, iLcColU):
                        LcTargetArray[iLcRowL, iLcCol] = LcSourceArray[iLcCol + 1 - iLcColL]
                else:
                    for iLcCol in range(iLcColL, iLcColU):
                        LcTargetArray[iLcCol] = LcSourceArray[iLcCol + 1 - iLcColL]
            else:
                if iLcDim == 2:
                    for iLcCol in range(iLcColL, iLcColU):
                        LcTargetArray[iLcRowL, iLcCol] = LcSourceArray[1, iLcCol + 1 - iLcColL]
                else:
                    for iLcCol in range(iLcColL, iLcColU):
                        LcTargetArray[iLcCol] = LcSourceArray[1, iLcCol + 1 - iLcColL]
        elif iLcColL == iLcColU:
            if iLcDim == 2:
                for iLcRow in range(iLcRowL, iLcRowU):
                    LcTargetArray[iLcRow, iLcColL] = LcSourceArray[iLcRow + 1 - iLcRowL]
            else:
                for iLcRow in range(iLcRowL, iLcRowU):
                    LcTargetArray[iLcRow] = LcSourceArray[iLcRow + 1 - iLcRowL]
        else:
            for iLcRow in range(iLcRowL, iLcRowU):
                for iLcCol in range(iLcColL, iLcColU):
                    LcTargetArray[iLcRow, iLcCol] = LcSourceArray[iLcRow + 1 - iLcRowL, iLcCol + 1 - iLcColL]
    else:
        if iLcRowL == iLcRowU and iLcDim == 1:
            for iLcCol in range(iLcColL, iLcColU):
                LcTargetArray[iLcCol] = LcSourceArray
        elif iLcColL == iLcColU and iLcDim == 1:
            for iLcRow in range(iLcRowL, iLcRowU):
                LcTargetArray[iLcRow] = LcSourceArray
        else:
            for iLcRow in range(iLcRowL, iLcRowU):
                for iLcCol in range(iLcColL, iLcColU):
                    LcTargetArray[iLcRow, iLcCol] = LcSourceArray

if __name__ == '__main__':
    import os, traceback

    try:
        PHEVT_Consumer()
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
