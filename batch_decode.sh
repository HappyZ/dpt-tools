for each in $(find ./extracted_apk -type f -name "*.odex");
do
    mkdir ${each%/*}/out;
    java -jar ../dex2jar/oat2dex.jar -o ${each%/*} odex $each;
    java -jar ../dex2jar/baksmali-2.2.4.jar disassemble ${each/odex/dex} -o ${each%/*}/out
    java -jar ../dex2jar/smali-2.2.4.jar assemble ${each%/*}/out -o ${each/odex/dex}
    ../dex2jar/d2j-dex2jar.sh ${each/odex/dex} -o ${each%.*}.jar;
    rm -rf ${each%/*}/out
done

for each in $(find ./extracted_apk -type f -name "*.apk");
do
    mkdir ${each%/*}/out;
    apktool d $each -o ${each%/*}/out -f;
done