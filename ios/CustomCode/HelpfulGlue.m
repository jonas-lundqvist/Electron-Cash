//
//  HelpfulGlue.m
//  Electron-Cash
//
//  Created by calin on 2/23/18.
//  Copyright © 2018 Calin Culianu. All rights reserved.
//

#import <Foundation/Foundation.h>
#import <UIKit/UIKit.h>
#include <Python.h>

@interface HelpfulGlue : NSObject {
}
@end

@implementation HelpfulGlue
// NB: This will always evaluate the python in the main thread and can be called from any thread!
// Useful for passing off work from subthreads to the main thread (can use delay=0)
// Note 2: This is kind of buggy because.. Python.  Use python-only code from call_later() in ios_natic/utils.py, etc.
+ (NSUInteger) evalPython:(NSString *)python afterDelay:(NSTimeInterval)delay {
    if (!python || !python.length) return 0;
    @autoreleasepool { // might be needed because python thread context might not have an autorelease pool and bad things can happen..?
        __block NSString *thePython = python;
        NSTimer *t = [NSTimer timerWithTimeInterval:delay repeats:NO block:^(NSTimer *t){
            thePython = [NSString stringWithFormat:@"timer_ptr=%lu\n\n%@",(unsigned long)t, thePython];
            PyRun_SimpleString(thePython.UTF8String);
        }];

        [NSRunLoop.mainRunLoop addTimer:t forMode:NSDefaultRunLoopMode];
        return (NSUInteger)t;
    }
}
@end

