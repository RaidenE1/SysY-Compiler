declare i32 @getch()
declare void @putch(i32)
declare i32 @getint()
declare void @putint(i32)
define dso_local i32 @main ( ) {
%x1 = alloca i32
%x2 = call i32 @getint()
store i32 %x2, i32* %x1 
%x3 = alloca i32
%x4 = call i32 @getint()
store i32 %x4, i32* %x3 
%x5 = load i32, i32* %x1
%x6 = load i32, i32* %x3
%x7 = icmp sle i32 %x5, %x6
br i1 %x7, label %x8, label %x9
x8:
call void @putint(i32 1)

br label %x9
x9:
call void @putint(i32 0)

ret i32 0
}
