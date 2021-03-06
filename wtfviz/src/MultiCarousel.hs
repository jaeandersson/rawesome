{-# OPTIONS_GHC -Wall #-}
{-# Language DoAndIfThenElse #-}
{-# Language OverloadedStrings #-}
{-# Language CPP #-}

module Main ( main ) where

import Data.Foldable ( toList )
import Data.Maybe ( fromMaybe )
#if OSX
import qualified System.ZMQ3 as ZMQ
#else
import qualified System.ZMQ as ZMQ
#endif
import Control.Concurrent ( MVar, forkIO, modifyMVar_, newMVar, readMVar)
import Control.Monad ( forever, when )
import qualified Data.ByteString.Lazy as BL
import Data.Packed ( fromLists )
import Text.ProtocolBuffers ( messageGet )
import Text.ProtocolBuffers.Basic ( uToString )
--import System.Remote.Monitoring ( forkServer )

import qualified Kite.MultiCarousel as MC
import qualified Kite.CarouselState as CS
import qualified Kite.Dcm as Dcm
import qualified Kite.Xyz as KiteXyz

import SpatialMath
import qualified Xyz
import Vis
import DrawAC
import ParseArgs ( getip )

type State = Maybe MC.MultiCarousel

data NiceKite = NiceKite { nk_xyz :: Xyz Double
                         , nk_q'n'b :: Quat Double
                         , nk_r'n0'a0 :: Xyz Double
                         , nk_r'n0't0 :: Xyz Double
                         , nk_lineAlpha :: Float
                         , nk_kiteAlpha :: Float
                         , nk_visSpan :: Double
                         }

toNice :: CS.CarouselState -> NiceKite
toNice cs = NiceKite { nk_xyz = xyz
                     , nk_q'n'b = q'n'b
                     , nk_r'n0'a0 = r'n0'a0
                     , nk_r'n0't0 = r'n0't0
                     , nk_lineAlpha = realToFrac $ fromMaybe 1 (CS.lineTransparency cs)
                     , nk_kiteAlpha = realToFrac $ fromMaybe 1 (CS.kiteTransparency cs)
                     , nk_visSpan = fromMaybe 1 (CS.visSpan cs)
                     }
  where
    x = KiteXyz.x $ CS.kiteXyz cs
    y = KiteXyz.y $ CS.kiteXyz cs
    z = KiteXyz.z $ CS.kiteXyz cs
    
    r11 = Dcm.r11 $ CS.kiteDcm cs
    r12 = Dcm.r12 $ CS.kiteDcm cs
    r13 = Dcm.r13 $ CS.kiteDcm cs

    r21 = Dcm.r21 $ CS.kiteDcm cs
    r22 = Dcm.r22 $ CS.kiteDcm cs
    r23 = Dcm.r23 $ CS.kiteDcm cs

    r31 = Dcm.r31 $ CS.kiteDcm cs
    r32 = Dcm.r32 $ CS.kiteDcm cs
    r33 = Dcm.r33 $ CS.kiteDcm cs

    delta = CS.delta cs

    q'nwu'ned = Quat 0 1 0 0

    q'n'a = Quat (cos(0.5*delta)) 0 0 (sin(-0.5*delta))

    q'aNWU'bNWU = quatOfDcm $ fromLists [ [r11, r12, r13]
                                        , [r21, r22, r23]
                                        , [r31, r32, r33]
                                        ]
    q'a'b = q'nwu'ned * q'aNWU'bNWU * q'nwu'ned
    q'n'b = q'n'a * q'a'b
    q'n'aNWU = q'n'a * q'nwu'ned

    rArm = Xyz (CS.rArm cs) 0 0
    xyzArm = rArm + Xyz x y z
    xyz = rotVecByQuatB2A q'n'aNWU xyzArm

    zt = CS.zt cs
    r'n0'a0 = rotVecByQuatB2A q'n'a rArm
    r'n0't0 = xyz + (rotVecByQuatB2A q'n'b $ Xyz 0 0 (-zt))

drawOneKite :: Double -> NiceKite -> (VisObject Double, Double)
drawOneKite minLineLength niceKite
  | nk_lineAlpha niceKite > 0 = (VisObjects [ac, arm, line], z)
  | otherwise = (ac, z)
  where
    pos@(Xyz _ _ z) = nk_xyz niceKite
    quat = nk_q'n'b niceKite
    r'n0'a0 = nk_r'n0'a0 niceKite
    r'n0't0 = nk_r'n0't0 niceKite
    
    arm  = Line [Xyz 0 0 0, r'n0'a0] $ makeColor 1 1 0 (nk_lineAlpha niceKite)
    line = VisObjects [ line1 $ makeColor 1 0.2 0 (nk_lineAlpha niceKite)
                      , line2 $ makeColor 0 1 1 (nk_lineAlpha niceKite)
                      ]
      where
        line1 = Line [r'n0'a0, rMid] 
        line2 = Line [rMid, r'n0't0] 

        rMid = r'n0'a0 + fmap (* (1 - minLineLength/normDr)) dr
        dr = r'n0't0 - r'n0'a0
        normDr = Xyz.norm dr
        

    s = nk_visSpan niceKite
    ac = Trans pos $ Scale (s,s,s) ac'
    (ac',_) = drawAc (nk_kiteAlpha niceKite) (Xyz 0 0 0) quat

drawFun :: State -> VisObject Double
drawFun Nothing = VisObjects []
drawFun (Just ko) = VisObjects $ [axes,txt] ++ [plane] ++ kites
  where
    niceKites = map toNice (toList (MC.horizon ko))

    minLineLength = minimum $ map lineLength niceKites
      where
        lineLength nk = Xyz.norm (nk_r'n0't0 nk - nk_r'n0'a0 nk)

    (kites,zs) = unzip $ map (drawOneKite minLineLength) niceKites
    z = maximum zs
--    points = Points (sParticles state) (Just 2) $ makeColor 1 1 1 0.5
    
    axes = Axes (0.5, 15)
--    arm  = Line [Xyz 0 0 0, r'n0'a0] $ makeColor 1 1 0 1
--    line = Line [r'n0'a0, r'n0't0]   $ makeColor 0 1 1 1
    plane = Trans (Xyz 0 0 planeZ') $ Plane (Xyz 0 0 1) (makeColor 1 1 1 1) (makeColor 0.2 0.3 0.32 planeAlpha)

    planeZ' = 2
    planeAlpha = 1*planeAlphaFade + (1 - planeAlphaFade)*0.2
    planeAlphaFade
      | z < planeZ' = 1
      | z < planeZ'+2 = realToFrac $ (planeZ'+2-z)/2
      | otherwise = 0
--    text k = 2dText "KITEVIS 4EVER" (100,500 - k*100*x) TimesRoman24 (makeColor 0 (0.5 + x'/2) (0.5 - x'/2) 1)
--      where
--        x' = realToFrac $ (x + 1)/0.4*k/5
--    boxText = 3dText "I'm a plane" (Xyz 0 0 (x-0.2)) TimesRoman24 (makeColor 1 0 0 1)
--    ddelta = CS.ddelta cs

--    (u1,u2,tc,wind_x) = (CS.u1 cs, CS.u2 cs, CS.tc cs, CS.wind_x cs)
    txt = VisObjects $
          zipWith (\s k -> Text2d (uToString s) (30,fromIntegral $ 30*k) TimesRoman24 (makeColor 1 1 1 1)) messages (reverse [1..length messages])
    messages = toList $ MC.messages ko


updateState :: MC.MultiCarousel -> State -> IO State
updateState ko _ = return $ Just ko

withContext :: (ZMQ.Context -> IO a) -> IO a
#if OSX
withContext = ZMQ.withContext
#else
withContext = ZMQ.withContext 1
#endif

sub :: String -> MVar State -> IO ()
sub ip m = withContext $ \context -> do
#if OSX
  let receive = ZMQ.receive
#else
  let receive = flip ZMQ.receive []
#endif
  ZMQ.withSocket context ZMQ.Sub $ \subscriber -> do
    ZMQ.connect subscriber ip
    ZMQ.subscribe subscriber "multi-carousel"
    forever $ do
      _ <- receive subscriber
      mre <- ZMQ.moreToReceive subscriber
      if mre
      then do
        msg <- receive subscriber
        let cs = case messageGet (BL.fromChunks [msg]) of
              Left err -> error err
              Right (cs',_) -> cs'
        modifyMVar_ m (updateState cs)
      else return ()

ts :: Double
ts = 0.02

main :: IO ()
main = do
--  _ <- forkServer "localhost" 8000
  (ip,followkite) <- getip "multicarousel" "tcp://localhost:5563"
  when followkite $ putStrLn "multicarousel doesn't respect followkite flag, yo"
  putStrLn $ "using ip \""++ip++"\""

  m <- newMVar Nothing
  _ <- forkIO (sub ip m)
  
--  threadDelay 5000000
  let simFun _ _ = return ()
      df _ = fmap drawFun (readMVar m)
  simulateIO (Just ((1260,940),(1930,40))) "multi-carousel" ts () df simFun
