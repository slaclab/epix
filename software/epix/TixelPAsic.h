//-----------------------------------------------------------------------------
// File          : TixelPAsic.h
// Author        : Maciej Kwiatkowski  <mkwiatko@slac.stanford.edu>
// Created       : 06/06/2013
// Project       : TIXEL Prototype ASIC
//-----------------------------------------------------------------------------
// Description :
// EPIX ASIC container
//-----------------------------------------------------------------------------
// This file is part of 'EPIX Development Softare'.
// It is subject to the license terms in the LICENSE.txt file found in the 
// top-level directory of this distribution and at: 
//    https://confluence.slac.stanford.edu/display/ppareg/LICENSE.html. 
// No part of 'EPIX Development Softare', including this file, 
// may be copied, modified, propagated, or distributed except according to 
// the terms contained in the LICENSE.txt file.
// Proprietary and confidential to SLAC.
//-----------------------------------------------------------------------------
// Modification history :
// 03/07/2016: created
//-----------------------------------------------------------------------------
#ifndef __TIXELP_ASIC_H__
#define __TIXELP_ASIC_H__

#include <Device.h>
using namespace std;

//! Class to contain Kpix ASIC
class TixelPAsic : public Device {

   public:

      //! Constructor
      /*! 
       * \param destination Device destination
       * \param baseAddress Device base address
       * \param index       Device index
       * \param parent      Parent device
      */
      TixelPAsic ( uint destination, uint baseAddress, uint index, Device *parent, uint addrSize );

      //! Deconstructor
      ~TixelPAsic ( );

      //! Method to process a command
      /*!
       * Returns status string if locally processed. Otherwise
       * an empty string is returned.
       * \param name     Command name
       * \param arg      Optional arg
      */
      void command ( string name, string arg );

      //! Method to read status registers and update variables
      /*! 
       * Throws string on error.
      */
      void readStatus ( );

      //! Method to read configuration registers and update variables
      /*! 
       * Throws string on error.
      */
      void readConfig ( );

      //! Method to write configuration registers
      /*! 
       * Throws string on error.
       * \param force Write all registers if true, only stale if false
      */
      void writeConfig ( bool force );

      //! Verify hardware state of configuration
      void verifyConfig ( );

};
#endif
