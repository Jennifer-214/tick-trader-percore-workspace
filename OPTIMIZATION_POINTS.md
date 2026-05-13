# PRUNED SITES FOR OPTIMIZATION
    - Im going to hand verify the slowpath to try and identify points of OPTIMIZATION

# FILES TO LOOK THROUGH
    - CoreFrameworks/ControllerEventLoop.hpp
    - Strategies/StrategyParameters.hpp
    - ML_Headers/RollingStats.hpp
    - Strategies/RegimeDetector.hpp
    - ML_Headers/CoreModelZoo.hpp
    - ML_Headers/ConfidenceScore.hpp
    - CoreFrameworks/EngineSharded.hpp
    - CoreFrameworks/OrderManager.hpp
    - ML_Headers/FlowFeatures.hpp

# RECOMMENDED ORDER
    - ML_BuildParameters in StrategyParameters.hpp
    - RollingStats::push in RollingStats.hpp
    - EventLoop_RebuildOneCore in ControllerEventLoop.hpp
    - Regime_ComputeSignals in RegimeDetector.hpp
    - HandleFill + DrainPostFill in OrderManager.hpp + ControllerEventLoop.hpp

# FINDINGS
    - Mark fingins with a grep searchable note like
    **USER_IDENTIFIED**



