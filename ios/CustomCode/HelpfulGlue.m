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
@end

@implementation HelpfulGlue
@synthesize dict;

- (instancetype) init {
    self = [super init];
    self.dict = [NSMutableDictionary dictionaryWithCapacity:100];
    return self;
}

- (void) dealloc {
    self.dict = nil;
    // called by compiler: [super dealloc];
}

+ (HelpfulGlue *)instance {
    static HelpfulGlue *ins = nil;

    if (!ins) ins = [HelpfulGlue new];
    return ins;
}

+ (UIAlertAction *) actionWithTitle:(NSString *)title style:(UIAlertActionStyle)style python:(NSString *)pyth {
    __block HelpfulGlue *slf = [HelpfulGlue instance];
    UIAlertAction *ret;
    ret = [UIAlertAction actionWithTitle:title style:style handler:^(UIAlertAction *act) {
        NSString *pyth = nil;
        for (NSNumber *n in slf.dict) {
            unsigned long val = [n unsignedLongValue];
            if (val == (unsigned long)act) {
                pyth = slf.dict[n];
//                NSLog(@"Found the python: '%@'", pyth);
                pyth = [NSString stringWithFormat:@"action_ptr=%ld\naction_title='''%@'''\n\n%@",(long)act,act.title,pyth];
                break;
            }
        }
        if (pyth) {
//            NSLog(@"Executing python.. lord help us..");
            PyRun_SimpleString(pyth.UTF8String);
            [slf.dict removeObjectForKey:pyth];
        } else {
            NSLog(@"Handler called but python not found for object '%@'",[act description]);
        }
    }];
    NSNumber *n = [NSNumber numberWithUnsignedLongLong:(unsigned long long)ret];
    slf.dict[n] = pyth;
    return ret;
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
            thePython = [NSString stringWithFormat:@"vc_ptr=%ld\nmvc_ptr=%ld\n\n%@",vc_ptr, mvc_ptr, thePython];
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
            thePython = [NSString stringWithFormat:@"vc_ptr=%ld\n\n%@",vc_ptr, thePython];
            PyRun_SimpleString(thePython.UTF8String);
        }];
    }
}

@end

