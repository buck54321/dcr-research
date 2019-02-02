"""
Mainnet holds mainnet parameters. Any values should mirror exactly
https://github.com/decred/dcrd/blob/master/chaincfg/mainnetparams.go
"""
import pydecred.constants as C

# POW parameters
PowLimitBitsf = 0x1d00ffff
ReduceMinDifficultyf = False
MinDiffReductionTimef = 0
GenerateSupportedf = False
MaximumBlockSizesf = [393216]
MaxTxSizef = 393216
TargetTimePerBlock = C.MINUTE * 5
WorkDiffAlphaf = 1
WorkDiffWindowSizef = 144
WorkDiffWindowsf = 20
TargetTimespanf = C.MINUTE * 5 * 144  # TimePerBlock * WindowSize
RetargetAdjustmentFactorf = 4

# Subsidy parameters.
BaseSubsidy = 3119582664  			# 21m
MulSubsidy = 100
DivSubsidy = 101
SubsidyReductionInterval = 6144
WorkRewardProportion = 6
StakeRewardProportion = 3
BlockTaxProportion = 1

# Decred PoS parameters
MinimumStakeDiff = 2 * 1e8 			# 2 Coin
TicketPoolSize = 8192
TicketsPerBlock = 5
TicketMaturity = 256
TicketExpiry = 40960  				# 5*TicketPoolSize
CoinbaseMaturity = 256
SStxChangeMaturity = 1
TicketPoolSizeWeight = 4
StakeDiffAlpha = 1  				# Minimal
StakeDiffWindowSize = 144
StakeDiffWindows = 20
StakeVersionInterval = 144 * 2 * 7  # ~1 week
MaxFreshStakePerBlock = 20          # 4*TicketsPerBlock
StakeEnabledHeight = 256 + 256   	# CoinbaseMaturity + TicketMaturity
StakeValidationHeight = 4096        # ~14 days
StakeBaseSigScript = [0, 0]
StakeMajorityMultiplier = 3
StakeMajorityDivisor = 4

# Convenience constants
GENESIS_STAMP = 1454954400
REWARD_WINDOW_SIZE = 6144
STAKE_SPLIT = 0.3
POW_SPLIT = 0.6
TREASURY_SPLIT = 0.1