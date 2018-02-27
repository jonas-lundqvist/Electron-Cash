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
    NSMutableDictionary *dict;
}
@property (strong,nonatomic) NSMutableDictionary *dict;
@property (nonatomic,class,readonly) HelpfulGlue *instance;
@end

@implementation HelpfulGlue
@synthesize dict;

static HelpfulGlue *ins = nil;

- (instancetype) init {
    self = [super init];
    self.dict = [NSMutableDictionary dictionaryWithCapacity:100];
    return self;
}

- (void) dealloc {
    self.dict = nil;
    if (self == ins) ins = nil;
    //NSLog(@"HelpfulGlue dealloc");
    // called by compiler: [super dealloc];
}

+ (HelpfulGlue *)instance {
    if (!ins) ins = [HelpfulGlue new];
    return ins;
}

+ (UIAlertAction *) actionWithTitle:(NSString *)title style:(UIAlertActionStyle)style python:(NSString *)pyth {
    return [HelpfulGlue.instance actionWithTitle:title style:style python:pyth];
}

- (UIAlertAction *) actionWithTitle:(NSString *)title style:(UIAlertActionStyle)style python:(NSString *)pyth {
    __block HelpfulGlue *slf = self;
    UIAlertAction *ret;
    if (pyth) {
        ret = [UIAlertAction actionWithTitle:title style:style handler:^(UIAlertAction *act) {
            NSString *pyth = nil;
            for (NSNumber *n in slf.dict) {
                unsigned long val = [n unsignedLongValue];
                if (val == (unsigned long)act) {
                    pyth = slf.dict[n];
                    //                NSLog(@"Found the python: '%@'", pyth);
                    pyth = [NSString stringWithFormat:@"action_ptr=%lu\naction_title='''%@'''\n\n%@",(unsigned long)act,act.title,pyth];
                    break;
                }
            }
            if (pyth) {
                //            NSLog(@"Executing python.. lord help us..");
                PyRun_SimpleString(pyth.UTF8String);
                // NB: python handler should call [slf clearCallbacksTable] at some point otherwise this will leak!
                //            [slf.dict removeObjectForKey:pyth];
            } else {
                NSLog(@"Handler called but python not found for object '%@'",[act description]);
            }
        }];
        NSNumber *n = [NSNumber numberWithUnsignedLong:(unsigned long)ret];
        self.dict[n] = pyth;
    } else {
        ret = [UIAlertAction actionWithTitle:title style:style handler:nil];
    }
    return ret;
}

+ (void) clearCallbacksTable {
    [self.instance clearCallbacksTable];
}

- (void) clearCallbacksTable {
    //NSUInteger ct = self.dict.count;
    [self.dict removeAllObjects];
    //NSLog(@"HelpfulGlue callbacks table cleared %d entries!",(int)ct);
}

+ (void) viewController:(UIViewController *)vc presentModalViewController:(UIViewController *)mvc animated:(BOOL)anim
                 python:(NSString *)python {
    if (!python || !python.length)
        [vc presentViewController:mvc animated:anim completion:nil];
    else {
        __block NSString *thePython = python;
        __block unsigned long vc_ptr = (unsigned long)vc;
        __block unsigned long mvc_ptr = (unsigned long)mvc;
        [vc presentViewController:mvc animated:anim completion:^{
//            NSLog(@"Executing python.. lord help us..");
            thePython = [NSString stringWithFormat:@"vc_ptr=%lu\nmvc_ptr=%lu\n\n%@",(unsigned long)vc_ptr, (unsigned long)mvc_ptr, thePython];
            PyRun_SimpleString(thePython.UTF8String);
        }];
    }
}

+ (void) viewController:(UIViewController *)vc dismissModalViewControllerAnimated:(BOOL)anim
                 python:(NSString *)python {
    if (!python || !python.length)
        [vc dismissViewControllerAnimated:anim completion:nil];
    else {
        __block NSString *thePython = python;
        __block unsigned long vc_ptr = (unsigned long)vc;
        [vc dismissViewControllerAnimated:anim completion:^{
            //            NSLog(@"Executing python.. lord help us..");
            thePython = [NSString stringWithFormat:@"vc_ptr=%lu\n\n%@",(unsigned long)vc_ptr, thePython];
            PyRun_SimpleString(thePython.UTF8String);
        }];
    }
}

// NB: This will always evaluate the python in the main thread and can be called from any thread!
// Useful for passing off work from subthreads to the main thread (can use delay=0)
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

