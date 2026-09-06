#include "RooDataHist.h"
#include "RooWorkspace.h"
#include "RooRealVar.h"
#include "RooAbsPdf.h"
#include "RooPlot.h"
#include "RooFitResult.h"
#include "TH1.h"
#include "TSystem.h"
#include "TFile.h"
#include "TCanvas.h"
#include "TPaveText.h"

/// include pdfs
#include "RooCBExGaussShape.h"
#include "RooCMSShape.h"

#include <vector>
#include <string>
#include <algorithm>
#include <cmath>
#include <cstdlib>
#ifdef __CINT__
#pragma link C++ class std::vector<std::string>+;
#endif

using namespace RooFit;
using namespace std;

class tnpFitter {
public:
  tnpFitter( TFile *file, std::string histname  );
  tnpFitter( TH1 *hPass, TH1 *hFail, std::string histname  );
  ~tnpFitter(void) {if( _work != 0 ) delete _work; }
  void setZLineShapes(TH1 *hZPass, TH1 *hZFail );
  void setWorkspace(std::vector<std::string>, bool isaddGaus=false);
  void setOutputFile(TFile *fOut ) {_fOut = fOut;}
  void fits(bool mcTruth,bool isMC,std::string title = "", bool isaddGaus=false);
  void useMinos(bool minos = true) {_useMinos = minos;}
  void textParForCanvas(RooFitResult *resP, RooFitResult *resF, TPad *p);
  
  void fixSigmaFtoSigmaP(bool fix=true) { _fixSigmaFtoSigmaP= fix;}

  void setFitRange(double xMin,double xMax) { _xFitMin = xMin; _xFitMax = xMax; }
private:
  RooWorkspace *_work;
  std::string _histname_base;
  TFile *_fOut;
  double _nTotP, _nTotF;
  bool _useMinos;
  bool _fixSigmaFtoSigmaP;
  double _xFitMin,_xFitMax;
  int _nBins = 10000;
};

tnpFitter::tnpFitter(TFile *filein, std::string histname   ) : _useMinos(false),_fixSigmaFtoSigmaP(false) {
  RooMsgService::instance().setGlobalKillBelow(RooFit::WARNING);
  _histname_base = histname;  

  TH1 *hPass = (TH1*) filein->Get(TString::Format("%s_Pass",histname.c_str()).Data());
  TH1 *hFail = (TH1*) filein->Get(TString::Format("%s_Fail",histname.c_str()).Data());
  _nTotP = hPass->Integral();
  _nTotF = hFail->Integral();
  /// MC histos are done between 50-130 to do the convolution properly
  /// but when doing MC fit in 60-120, need to zero bins outside the range
  for( int ib = 0; ib <= hPass->GetXaxis()->GetNbins()+1; ib++ )
   if(  hPass->GetXaxis()->GetBinCenter(ib) <= 60 || hPass->GetXaxis()->GetBinCenter(ib) >= 120 ) {
     hPass->SetBinContent(ib,0);
     hFail->SetBinContent(ib,0);
   }
  
  _work = new RooWorkspace("w") ;
  _work->factory("x[50,130]");

  RooDataHist rooPass("hPass","hPass",*_work->var("x"),hPass);
  RooDataHist rooFail("hFail","hFail",*_work->var("x"),hFail);
  _work->import(rooPass) ;
  _work->import(rooFail) ;
  _xFitMin = 60;
  _xFitMax = 120;
}

tnpFitter::tnpFitter(TH1 *hPass, TH1 *hFail, std::string histname  ) : _useMinos(false),_fixSigmaFtoSigmaP(false) {
  RooMsgService::instance().setGlobalKillBelow(RooFit::WARNING);
  _histname_base = histname;
  
  _nTotP = hPass->Integral();
  _nTotF = hFail->Integral();
  /// MC histos are done between 50-130 to do the convolution properly
  /// but when doing MC fit in 60-120, need to zero bins outside the range
  for( int ib = 0; ib <= hPass->GetXaxis()->GetNbins()+1; ib++ )
    if(  hPass->GetXaxis()->GetBinCenter(ib) <= 60 || hPass->GetXaxis()->GetBinCenter(ib) >= 120 ) {
      hPass->SetBinContent(ib,0);
      hFail->SetBinContent(ib,0);
    }
  
  _work = new RooWorkspace("w") ;
  _work->factory("x[50,130]");
  
  RooDataHist rooPass("hPass","hPass",*_work->var("x"),hPass);
  RooDataHist rooFail("hFail","hFail",*_work->var("x"),hFail);
  _work->import(rooPass) ;
  _work->import(rooFail) ;
  _xFitMin = 60;
  _xFitMax = 120;
  
}


// ---------------------------------------------------------------------------
// MC template sanitisation (HZa 2026-09-06)
//
// setZLineShapes used to hand the raw MC histogram straight to HistPdf and
// from there into an FFT convolution, with no protection at all. Three things
// go wrong when the template runs out of statistics, and none of them show up
// in edm or covQual -- the fit reports covQual=3 with a tiny edm while MIGRAD
// has not moved a single parameter off its seed:
//
//   1. Negative bins. NLO DY carries negative event weights, so low-statistics
//      bins can go below zero. HistPdf then returns pdf<0, getLogVal() is NaN,
//      and every MIGRAD probe comes back -inf.
//   2. Empty bins. A hard zero in the template is a sharp edge; the FFT rings
//      around it into small negative values -- same NaN, same frozen fit.
//      (Measured: elminiIso0p15 2024 bin03 has 30 empty bins out of 80;
//       phcsev hr9 2023postBPix bin01 has 75 out of 80.)
//   3. Single high-weight MC events. One event with weight ~7000 among typical
//      weights of 1-3 makes a spike the fit faithfully convolves into the
//      model. Measured on the muon side: a 115 GeV "peak" whose curve sat at
//      479 where the data had zero events.
//
// This is a port of the protection added to spark_tnp/TagAndProbeFitter.py on
// 2026-08-29, which is what let the muon refit turn that 479 into 6.
//
// The spike criterion is error/content, NOT "how many times the neighbours".
// Real physics structure has a small relative error; a single-event spike has
// a relative error near 1. THREE conditions must hold before a bin is touched
// -- the bin is much larger than its neighbours, the bin itself is poorly
// measured, and the neighbourhood is well measured enough for its median to
// be worth substituting -- and every change is printed, so none of this
// happens silently. See the comment at the criterion for why the third
// condition is not optional.
//
// Order matters: clamp negatives first (that creates more zeros), then remove
// spikes (the median must be computed before the floor flattens the zeros),
// then floor whatever is still empty.
//
// Set TNP_NO_TEMPLATE_SANITIZE=1 to switch the whole thing off (for A/B
// comparison against the old behaviour).
namespace {

void tnpSanitizeTemplate(TH1 *h, const char *tag, const std::string &name) {
  if( h == 0 ) return;
  if( getenv("TNP_NO_TEMPLATE_SANITIZE") != 0 ) return;
  const int nb = h->GetNbinsX();
  if( nb < 3 ) return;

  // (1) negative bins -> 0, keeping |c| as the error so the bin stays
  //     un-trusted rather than looking like a precise zero.
  int nneg = 0; double negSum = 0.0;
  for( int i = 1; i <= nb; ++i ) {
    const double c = h->GetBinContent(i);
    if( c < 0.0 ) { ++nneg; negSum += c; h->SetBinContent(i,0.0); h->SetBinError(i,std::fabs(c)); }
  }
  if( nneg )
    printf("[TnP] %s %s: clamped %d negative bins (sum %.3f) to zero\n",
           name.c_str(), tag, nneg, negSum);

  // (2) single high-weight event spikes -> local median.
  //     Snapshot the contents first: replacing in place while still reading
  //     would let one spike shift the median seen by the next bin.
  std::vector<double> vals(nb+1, 0.0);
  for( int i = 1; i <= nb; ++i ) vals[i] = h->GetBinContent(i);
  int nspike = 0;
  for( int i = 1; i <= nb; ++i ) {
    const double c = vals[i], e = h->GetBinError(i);
    if( c <= 0.0 ) continue;
    const int lo = std::max(1,i-3), hi = std::min(nb,i+3);
    std::vector<double> nbv;
    for( int j = lo; j <= hi; ++j ) if( j != i ) nbv.push_back(vals[j]);
    if( nbv.empty() ) continue;
    std::sort(nbv.begin(), nbv.end());
    const double med = nbv[nbv.size()/2];
    // The median is only worth substituting if the neighbourhood is itself
    // better measured than the candidate. On the muon side that was implicit
    // -- the spike had err/content 0.739 against neighbours at 0.02-0.04 --
    // and porting the criterion without that assumption misfires badly.
    //
    // Measured on dielleg23_nongap_2024 bin38 GenFail (eta 1.57-2.00,
    // ET 50-100): every bin from 50 to 80 GeV has err/content between 0.43
    // and 1.00, and a value of exactly 1.00 means the bin literally holds one
    // event. The four bins flagged as "spikes" there (0.46-0.60) were in fact
    // the best-measured bins in the region, and the local median offered as
    // their replacement was itself a single-event bin. Replacing them removed
    // ~110k events from the low-mass side of the template and the fit stopped
    // converging -- a bin that had been healthy (edm 4.4e-05, covQual 3)
    // timed out after 600 s.
    // So: require the neighbours' own median err/content to be below the same
    // 0.3 threshold. Where the whole region is statistics-starved there is no
    // trustworthy local shape to fall back on, and the honest thing is to
    // leave the template alone -- the empty-bin floor below still protects
    // against FFT ringing.
    std::vector<double> nbrel;
    for( int j = lo; j <= hi; ++j ) {
      if( j == i ) continue;
      const double cj = vals[j], ej = h->GetBinError(j);
      if( cj > 0.0 ) nbrel.push_back(ej/cj);
    }
    double medrel = 1.0;
    if( !nbrel.empty() ) {
      std::sort(nbrel.begin(), nbrel.end());
      medrel = nbrel[nbrel.size()/2];
    }
    if( med > 0.0 && c > 3.0*med && e/c > 0.3 && medrel < 0.3 ) {
      h->SetBinContent(i, med);
      h->SetBinError(i, std::sqrt(med));
      ++nspike;
      printf("[TnP] %s %s: spike at %.2f GeV content %.1f -> %.1f "
             "(err/content %.2f => single high-weight event)\n",
             name.c_str(), tag, h->GetBinCenter(i), c, med, e/c);
    }
  }
  if( nspike )
    printf("[TnP] %s %s: replaced %d single-event spike bin(s) with the local median\n",
           name.c_str(), tag, nspike);

  // (3) whatever is still empty gets a floor at 1e-6 of the mean bin content.
  //     Far below the statistical error on any real bin, but it removes the
  //     hard zero the FFT rings on.
  int nz = 0;
  for( int i = 1; i <= nb; ++i ) if( h->GetBinContent(i) <= 0.0 ) ++nz;
  if( nz ) {
    const double integ = h->Integral();
    if( integ > 0.0 ) {
      const double floorVal = 1e-6 * integ / double(nb);
      for( int i = 1; i <= nb; ++i )
        if( h->GetBinContent(i) <= 0.0 ) h->SetBinContent(i, floorVal);
      printf("[TnP] %s %s: floored %d empty bins to %.3e "
             "(1e-6 of mean; prevents FFT ringing -> NaN)\n",
             name.c_str(), tag, nz, floorVal);
    }
  }
  fflush(stdout);
}

} // namespace

void tnpFitter::setZLineShapes(TH1 *hZPass, TH1 *hZFail ) {
  // Work on clones, never on the caller's histograms. Two reasons:
  //   * fitUtils.py owns them via the TFile it closes straight afterwards;
  //   * in the high-pT branch it passes the SAME object as both Pass and Fail
  //     (histZLineShapeF = fileTruth.Get('..._Pass')), so sanitising in place
  //     would run over one histogram twice and compute the second pass's
  //     medians from already-modified content.
  TH1 *hP = (TH1*) hZPass->Clone(TString::Format("%s_genPassSane",_histname_base.c_str()).Data());
  TH1 *hF = (TH1*) hZFail->Clone(TString::Format("%s_genFailSane",_histname_base.c_str()).Data());
  hP->SetDirectory(0);
  hF->SetDirectory(0);
  tnpSanitizeTemplate(hP,"GenPass",_histname_base);
  tnpSanitizeTemplate(hF,"GenFail",_histname_base);
  RooDataHist rooPass("hGenZPass","hGenZPass",*_work->var("x"),hP);
  RooDataHist rooFail("hGenZFail","hGenZFail",*_work->var("x"),hF);
  _work->import(rooPass) ;
  _work->import(rooFail) ;
  delete hP;
  delete hF;
}

void tnpFitter::setWorkspace(std::vector<std::string> workspace, bool isaddGaus) {
  for( unsigned icom = 0 ; icom < workspace.size(); ++icom ) {
    _work->factory(workspace[icom].c_str());
  }

  _work->var("x")->setBins(_nBins, "cache");
  _work->factory("HistPdf::sigPhysPass(x,hGenZPass,1)");
  _work->factory("HistPdf::sigPhysFail(x,hGenZFail,1)");
  _work->factory("FCONV::sigPass(x, sigPhysPass , sigResPass)");
  _work->factory("FCONV::sigFail(x, sigPhysFail , sigResFail)");
  _work->factory(TString::Format("nSigP[%f,0.5,%f]",_nTotP*0.9,_nTotP*1.5));
  _work->factory(TString::Format("nBkgP[%f,0.5,%f]",_nTotP*0.1,_nTotP*1.5));
  _work->factory(TString::Format("nSigF[%f,0.5,%f]",_nTotF*0.9,_nTotF*1.5));
  _work->factory(TString::Format("nBkgF[%f,0.5,%f]",_nTotF*0.1,_nTotF*1.5));
  _work->factory("SUM::pdfPass(nSigP*sigPass,nBkgP*bkgPass)");
  
  if (isaddGaus) {
    _work->factory("SUM::pdfFail(expr('sigFracF*nSigF',{sigFracF,nSigF})*sigFail,nBkgF*bkgFail, expr('(1.-sigFracF)*nSigF',{sigFracF,nSigF})*sigGaussFail)");
  } 
  else {
    _work->factory("SUM::pdfFail(nSigF*sigFail,nBkgF*bkgFail)");
  }
  _work->Print();			         
}

void tnpFitter::fits(bool mcTruth,bool isMC,string title, bool isaddGaus) {

  cout << " title : " << title << endl;

  
  RooAbsPdf *pdfPass = _work->pdf("pdfPass");
  RooAbsPdf *pdfFail = _work->pdf("pdfFail");
  RooFitResult* resPass;
  RooFitResult* resFail;

  // If the workspace failed to build -- e.g. RooCBExGaussShapeTNP is absent from
  // the ROOT class table, so sigResFail, then sigFail, then pdfFail are never
  // created -- these come back null. Calling fitTo() on a null pdf segfaults,
  // and ROOT's signal handler then leaves the batch job hanging at ~2% CPU until
  // MaxRuntime kills it: the bin looks "still running" for hours and no amount of
  // resubmitting can fix it. Fail fast and loudly instead.
  if( !pdfPass || !pdfFail ) {
    cout << "[tnpFitter] ERROR: incomplete workspace for " << _histname_base
	 << " (pdfPass=" << (void*)pdfPass << ", pdfFail=" << (void*)pdfFail
	 << ") -- skipping this bin, nothing written." << endl;
    return;
  }

  if( mcTruth ) {
    _work->var("nBkgP")->setVal(0); _work->var("nBkgP")->setConstant();
    _work->var("nBkgF")->setVal(0); _work->var("nBkgF")->setConstant();
    if( _work->var("sosP")   ) { _work->var("sosP")->setVal(0);
      _work->var("sosP")->setConstant(); }
    if( _work->var("sosF")   ) { _work->var("sosF")->setVal(0);
      _work->var("sosF")->setConstant(); }
    if( _work->var("acmsP")  ) _work->var("acmsP")->setConstant();
    if( _work->var("acmsF")  ) _work->var("acmsF")->setConstant();
    if( _work->var("betaP")  ) _work->var("betaP")->setConstant();
    if( _work->var("betaF")  ) _work->var("betaF")->setConstant();
    if( _work->var("gammaP") ) _work->var("gammaP")->setConstant();
    if( _work->var("gammaF") ) _work->var("gammaF")->setConstant();
    if( _work->var("peakP") ) _work->var("peakP")->setConstant();
    if( _work->var("peakF") ) _work->var("peakF")->setConstant();

    // The names above cover RooCMSShape, which is what nominal and altSig use.
    // altBkg and altSigBkg use a RooExponential instead, and its slope
    // (alphaP/alphaF) is not in that list -- so with nBkg pinned to zero it had
    // nothing in the likelihood to constrain it and drifted to the edge of its
    // +-5 range, where exp(-alpha*m) across a 60-120 GeV window overflows. The
    // NLL stops being finite, the fit dies, and every error is left at exactly
    // zero: 55 of the 93 never-minimised electron sides are this, and the same
    // shape of failure dominates the photon measurements.
    //
    // Pin whatever the background pdfs actually depend on rather than naming
    // parameters, so a future background model cannot be missed the same way.
    // Doing it by dependency also keeps it away from altSig, where "alphaP" is
    // the Crystal Ball tail and has to stay free.
    const char *bkgPdfNames[2] = { "bkgPass", "bkgFail" };
    for( int ibkg = 0; ibkg < 2; ++ibkg ) {
      RooAbsPdf *bkgPdf = _work->pdf(bkgPdfNames[ibkg]);
      if( !bkgPdf ) continue;
      RooArgSet *bkgPars = bkgPdf->getParameters(*_work->var("x"));
      if( !bkgPars ) continue;
      for( RooAbsArg *arg : *bkgPars ) {
        RooRealVar *v = dynamic_cast<RooRealVar*>(arg);
        if( v ) v->setConstant(kTRUE);
      }
      delete bkgPars;
    }
  }

  // RooCMSShape's peak is degenerate: the likelihood has essentially no
  // curvature along it, so MnHesse reports a zero second derivative, the
  // Hessian comes back invalid, and RooFit marks the whole fit status -1 with
  // every error set to zero -- while still drawing a plausible curve from the
  // initial parameter values. That is what left 71% of the nominal fits (99% of
  // the data ones) silently unfitted. The mcTruth branch above already fixed
  // peak for MC, which is why MC survived far more often; do the same for data.
  if( _work->var("peakP") ) _work->var("peakP")->setConstant();
  if( _work->var("peakF") ) _work->var("peakF")->setConstant();

  /// FC: seems to be better to change the actual range than using a fitRange in the fit itself (???)
  /// FC: I don't know why but the integral is done over the full range in the fit not on the reduced range
  _work->var("x")->setRange(_xFitMin,_xFitMax);
  _work->var("x")->setRange("fitMassRange",_xFitMin,_xFitMax);
  // MINOS and SumW2Error are mutually exclusive in RooFit: with both on, fitTo()
  // prints "sum-of-weights and asymptotic error correction do not work with MINOS
  // errors. Not fitting." and returns a null pointer without minimising anything.
  // MC always needs SumW2Error (weighted histograms) and only histFitterNominal
  // turns MINOS on, so every nominal MC fit was silently skipped and then crashed
  // on the null result. MC efficiencies are cut-and-count anyway, so MINOS'
  // asymmetric errors are never used there -- drop MINOS for MC, keep it for data.
  const bool useMinosHere = _useMinos && ( isMC != 1 );
  if( isMC == 1 ) resPass = pdfPass->fitTo(*_work->data("hPass"), Minimizer("Minuit2", "MIGRAD"), Minos(useMinosHere), Strategy(2), SumW2Error(kTRUE),Save(),Range("fitMassRange"));
  else resPass = pdfPass->fitTo(*_work->data("hPass"), Minimizer("Minuit2", "MIGRAD"), Minos(useMinosHere), Strategy(2), SumW2Error(kFALSE),Save(),Range("fitMassRange"));
  //RooFitResult* resPass = pdfPass->fitTo(*_work->data("hPass"),Minos(_useMinos),SumW2Error(kTRUE),Save());
  if( _fixSigmaFtoSigmaP ) {
    _work->var("sigmaF")->setVal( _work->var("sigmaP")->getVal() );
    _work->var("sigmaF")->setConstant();
  }

  if( isMC == 1 ) resFail = pdfFail->fitTo(*_work->data("hFail"), Minimizer("Minuit2", "MIGRAD"), Minos(useMinosHere), Strategy(2), SumW2Error(kTRUE),Save(),Range("fitMassRange"));
  else resFail = pdfFail->fitTo(*_work->data("hFail"), Minimizer("Minuit2", "MIGRAD"), Minos(useMinosHere), Strategy(2), SumW2Error(kFALSE),Save(),Range("fitMassRange"));
  //RooFitResult* resFail = pdfFail->fitTo(*_work->data("hFail"),Minos(_useMinos),SumW2Error(kTRUE),Save());

  // fitTo() returns null whenever RooFit declines to fit at all. Dereferencing
  // that below (textParForCanvas does resP->status()) is the segfault that hangs
  // the job, so stop here instead -- the missing output file is then an honest
  // signal that this bin needs attention.
  if( !resPass || !resFail ) {
    cout << "[tnpFitter] ERROR: fitTo() returned no result for " << _histname_base
	 << " (resP=" << (void*)resPass << ", resF=" << (void*)resFail
	 << ") -- skipping this bin, nothing written." << endl;
    return;
  }

  RooPlot *pPass = _work->var("x")->frame(60,120);
  RooPlot *pFail = _work->var("x")->frame(60,120);
  pPass->SetTitle("passing probe");
  pFail->SetTitle("failing probe");
  
  _work->data("hPass") ->plotOn( pPass );
  _work->pdf("pdfPass")->plotOn( pPass, LineColor(kRed) );
  _work->pdf("pdfPass")->plotOn( pPass, Components("bkgPass"),LineColor(kBlue),LineStyle(kDashed));
  _work->data("hPass") ->plotOn( pPass );
  
  _work->data("hFail") ->plotOn( pFail );
  _work->pdf("pdfFail")->plotOn( pFail, LineColor(kRed) );
  _work->pdf("pdfFail")->plotOn( pFail, Components("bkgFail"),LineColor(kBlue),LineStyle(kDashed));
  _work->data("hFail") ->plotOn( pFail );

  TCanvas c("c","c",1100,450);
  c.Divide(3,1);
  TPad *padText = (TPad*)c.GetPad(1);
  textParForCanvas( resPass,resFail, padText );
  c.cd(2); pPass->Draw();
  c.cd(3); pFail->Draw();

  _fOut->cd();
  c.Write(TString::Format("%s_Canv",_histname_base.c_str()),TObject::kOverwrite);
  resPass->Write(TString::Format("%s_resP",_histname_base.c_str()),TObject::kOverwrite);
  resFail->Write(TString::Format("%s_resF",_histname_base.c_str()),TObject::kOverwrite);

  
}





/////// Stupid parameter dumper /////////
void tnpFitter::textParForCanvas(RooFitResult *resP, RooFitResult *resF,TPad *p) {

  double eff = -1;
  double e_eff = 0;

  RooRealVar *nSigP = _work->var("nSigP");
  RooRealVar *nSigF = _work->var("nSigF");
  
  double nP   = nSigP->getVal();
  double e_nP = nSigP->getError();
  double nF   = nSigF->getVal();
  double e_nF = nSigF->getError();
  double nTot = nP+nF;
  eff = nP / (nP+nF);
  e_eff = 1./(nTot*nTot) * sqrt( nP*nP* e_nF*e_nF + nF*nF * e_nP*e_nP );

  TPaveText *text1 = new TPaveText(0,0.8,1,1);
  text1->SetFillColor(0);
  text1->SetBorderSize(0);
  text1->SetTextAlign(12);

  text1->AddText(TString::Format("* fit status pass: %d, fail : %d",resP->status(),resF->status()));
  text1->AddText(TString::Format("* eff = %1.4f #pm %1.4f",eff,e_eff));

  //  text->SetTextSize(0.06);

//  text->AddText("* Passing parameters");
  TPaveText *text = new TPaveText(0,0,1,0.8);
  text->SetFillColor(0);
  text->SetBorderSize(0);
  text->SetTextAlign(12);
  text->AddText("    --- parmeters " );
  RooArgList listParFinalP = resP->floatParsFinal();
  for( int ip = 0; ip < listParFinalP.getSize(); ip++ ) {
    TString vName = listParFinalP[ip].GetName();
    text->AddText(TString::Format("   - %s \t= %1.3f #pm %1.3f",
				  vName.Data(),
				  _work->var(vName)->getVal(),
				  _work->var(vName)->getError() ) );
  }

//  text->AddText("* Failing parameters");
  RooArgList listParFinalF = resF->floatParsFinal();
  for( int ip = 0; ip < listParFinalF.getSize(); ip++ ) {
    TString vName = listParFinalF[ip].GetName();
    text->AddText(TString::Format("   - %s \t= %1.3f #pm %1.3f",
				  vName.Data(),
				  _work->var(vName)->getVal(),
				  _work->var(vName)->getError() ) );
  }

  p->cd();
  text1->Draw();
  text->Draw();
}
